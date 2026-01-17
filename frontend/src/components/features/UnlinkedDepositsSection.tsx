import { useState, useEffect, useCallback } from "react";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import axios from "axios";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Alert, AlertDescription } from "../ui/alert";
import { Spinner } from "../ui/spinner";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import { useTaskStore } from "../../stores/taskStore";
import { OperationType } from "../../services/WebSocketService";

interface UnlinkedDeposit {
  id: string;
  store: string;
  date: string;
  amount: string;
  doc_number: string;
  qb_url: string;
  has_cents: boolean;
}

interface UnlinkedDepositsResponse {
  deposits: UnlinkedDeposit[];
  summary: {
    count: number;
    total_amount: string;
  };
}

export function UnlinkedDepositsSection() {
  const [deposits, setDeposits] = useState<UnlinkedDeposit[]>([]);
  const [summary, setSummary] = useState<{ count: number; total_amount: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rerunningStore, setRerunningStore] = useState<string | null>(null);
  const { instance } = useMsal();
  const createImmediateTask = useTaskStore((state) => state.createImmediateTask);

  const getAccessToken = useCallback(async () => {
    const account = instance.getActiveAccount();
    if (!account) {
      throw new Error("No active account!");
    }

    try {
      const token = await instance.acquireTokenSilent({
        scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
        account,
      });
      return token.accessToken;
    } catch (tokenError) {
      if (tokenError instanceof InteractionRequiredAuthError) {
        try {
          const token = await instance.acquireTokenPopup({
            scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
            account,
          });
          return token.accessToken;
        } catch (popupError: unknown) {
          if (
            popupError &&
            typeof popupError === "object" &&
            ("errorCode" in popupError ||
              (popupError as { message?: string })?.message?.includes("popup") ||
              (popupError as { name?: string })?.name === "BrowserAuthError")
          ) {
            await instance.acquireTokenRedirect({
              scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
            });
            throw new Error("Authentication required. Please complete the redirect.");
          } else {
            throw popupError;
          }
        }
      } else {
        throw tokenError;
      }
    }
  }, [instance]);

  const fetchDeposits = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const accessToken = await getAccessToken();

      const client = axios.create({
        baseURL: API_BASE_URL,
      });

      const config = {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
      };

      const response = await client.get<UnlinkedDepositsResponse>(
        API_ENDPOINTS.UNLINKED_DEPOSITS,
        config
      );

      setDeposits(response.data.deposits);
      setSummary(response.data.summary);
    } catch (err) {
      console.error("Error fetching unlinked deposits:", err);
      setError("Failed to fetch unlinked deposits");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  const handleRerun = async (deposit: UnlinkedDeposit) => {
    const storeKey = `${deposit.store}-${deposit.date}`;
    setRerunningStore(storeKey);
    try {
      const accessToken = await getAccessToken();

      const client = axios.create({
        baseURL: API_BASE_URL,
      });

      // Parse the date to get year, month, day
      const [year, month, day] = deposit.date.split("-");

      const config = {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
      };

      // Use query parameters like the Daily Sales form does
      const params = new URLSearchParams({
        year,
        month,
        day,
        store: deposit.store,
      });

      const response = await client.post<{ task_id?: string }>(
        `${API_ENDPOINTS.DAILY_SALES}?${params}`,
        "",
        config
      );

      // Create immediate task notification if task_id is returned
      if (response.data.task_id) {
        createImmediateTask(response.data.task_id, OperationType.DAILY_SALES);
      }

      // Refresh the list after a short delay to allow processing
      setTimeout(() => {
        fetchDeposits();
      }, 5000);
    } catch (err) {
      console.error("Error re-running daily sales:", err);
      setError(`Failed to re-run daily sales for store ${deposit.store}`);
    } finally {
      setRerunningStore(null);
    }
  };

  useEffect(() => {
    fetchDeposits();
  }, [fetchDeposits]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + "T00:00:00");
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(parseFloat(amount));
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Unlinked Deposits</CardTitle>
          <CardDescription>
            Sales receipts in QuickBooks without linked bank deposits.
            Items with cents likely have missing FlexePOS entries.
          </CardDescription>
        </div>
        <Button variant="outline" onClick={fetchDeposits} disabled={loading}>
          {loading ? <Spinner className="h-4 w-4" /> : "Refresh"}
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && deposits.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Spinner className="h-8 w-8" />
          </div>
        ) : deposits.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No unlinked deposits found. All deposits are linked to bank transactions.
          </div>
        ) : (
          <>
            {summary && (
              <div className="mb-4 p-3 bg-muted rounded-lg flex gap-4">
                <span className="text-sm">
                  <strong>{summary.count}</strong> unlinked deposit{summary.count !== 1 ? "s" : ""}
                </span>
                <span className="text-sm">
                  Total: <strong>{formatCurrency(summary.total_amount)}</strong>
                </span>
              </div>
            )}

            <div className="overflow-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr>
                    <th className="text-left py-2 px-2">Date</th>
                    <th className="text-left py-2 px-2">Store</th>
                    <th className="text-right py-2 px-2">Amount</th>
                    <th className="text-left py-2 px-2">Doc #</th>
                    <th className="text-right py-2 px-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deposits.map((deposit) => {
                    const storeKey = `${deposit.store}-${deposit.date}`;
                    const isRerunning = rerunningStore === storeKey;
                    return (
                      <tr key={deposit.id} className="border-b hover:bg-muted/50">
                        <td className="py-2 px-2">{formatDate(deposit.date)}</td>
                        <td className="py-2 px-2">{deposit.store}</td>
                        <td className="py-2 px-2 text-right">
                          <span className="flex items-center justify-end gap-2">
                            {formatCurrency(deposit.amount)}
                            {deposit.has_cents && (
                              <Badge variant="warning" title="Amount has cents - likely missing FlexePOS entry">
                                !
                              </Badge>
                            )}
                          </span>
                        </td>
                        <td className="py-2 px-2 font-mono text-xs">{deposit.doc_number}</td>
                        <td className="py-2 px-2 text-right">
                          <div className="flex gap-1 justify-end">
                            <a
                              href={deposit.qb_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline"
                            >
                              View in QB
                            </a>
                            {deposit.has_cents && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => handleRerun(deposit)}
                                disabled={isRerunning}
                              >
                                {isRerunning ? <Spinner className="h-3 w-3" /> : "Re-run"}
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
