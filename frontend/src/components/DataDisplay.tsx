import { createClaimsTable } from "../utils/claimUtils";

interface IdTokenDataProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  idTokenClaims: any;
}

export function IdTokenData({ idTokenClaims }: IdTokenDataProps) {
  const tokenClaims = createClaimsTable(idTokenClaims);
  const claimEntries = Object.values(tokenClaims) as [string, string, string][];

  return (
    <div className="w-full max-w-4xl overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <caption className="mb-2 text-left text-sm font-semibold">
          ID Token Claims
        </caption>
        <thead>
          <tr className="border-b border-border bg-muted">
            <th className="min-w-[120px] max-w-[150px] border-r border-border p-2 text-left font-semibold">
              Claim
            </th>
            <th className="min-w-[200px] max-w-[300px] border-r border-border p-2 text-left font-semibold">
              Value
            </th>
            <th className="min-w-[200px] p-2 text-left font-semibold">
              Description
            </th>
          </tr>
        </thead>
        <tbody>
          {claimEntries.map(([claim, value, description], index) => (
            <tr
              key={claim}
              className={`border-b border-border ${
                index % 2 === 0 ? "bg-muted/20" : "bg-background"
              }`}
            >
              <td className="border-r border-border p-2 font-mono text-xs break-all">
                {claim}
              </td>
              <td className="border-r border-border p-2 font-mono text-xs break-all">
                {value}
              </td>
              <td className="p-2 text-xs break-words">
                {description}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
