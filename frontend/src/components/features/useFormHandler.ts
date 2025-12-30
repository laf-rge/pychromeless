import { useState } from "react";
import { useForm, SubmitHandler, DefaultValues } from "react-hook-form";
import axios, {
  AxiosResponse,
  AxiosRequestConfig,
  RawAxiosRequestHeaders,
  AxiosError,
} from "axios";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { FormValues, ApiConfig } from "./types";
import { logger } from "../../utils/logger";

export const useFormHandler = <T extends FormValues>(
  onSubmit: SubmitHandler<T>,
  apiConfig: ApiConfig
) => {
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting, isSubmitSuccessful },
    setValue,
    watch,
  } = useForm<T>({
    defaultValues: apiConfig.defaultValues as DefaultValues<T>,
  });
  const [error, setError] = useState<AxiosError>();
  const { instance } = useMsal();
  const activeAccount = instance.getActiveAccount();

  const submitForm = async (values: T) => {
    const client = axios.create({
      baseURL: apiConfig.baseURL,
    });

    let accessToken = "";
    if (activeAccount) {
      const accessTokenRequest = {
        scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
        account: activeAccount,
      };
      try {
        const accessTokenResponse = await instance.acquireTokenSilent(
          accessTokenRequest
        );
        accessToken = accessTokenResponse.accessToken;
      } catch (error) {
        logger.error(error);
        if (error instanceof InteractionRequiredAuthError) {
          try {
            await instance.acquireTokenPopup(accessTokenRequest);
            const accessTokenResponse = await instance.acquireTokenSilent(
              accessTokenRequest
            );
            accessToken = accessTokenResponse.accessToken;
          } catch (popupError: unknown) {
            if (
              popupError &&
              typeof popupError === "object" &&
              ("errorCode" in popupError ||
                (popupError as { message?: string })?.message?.includes("popup") ||
                (popupError as { name?: string })?.name === "BrowserAuthError")
            ) {
              logger.debug("Popup blocked, falling back to redirect");
              await instance.acquireTokenRedirect(accessTokenRequest);
            } else {
              throw popupError;
            }
          }
        } else {
          throw error;
        }
      }
    }

    const config: AxiosRequestConfig = {
      headers: {
        Accept: "application/json, text/csv",
        "Content-Type": "multipart/form-data",
        Authorization: `Bearer ${accessToken}`,
      } as RawAxiosRequestHeaders,
    };

    try {
      setError(undefined);
      let response: AxiosResponse;

      if (apiConfig.formDataSubmission) {
        const formData = new FormData();
        if (values.mp) {
          formData.append("year", values.mp.year.toString());
          formData.append("month", (values.mp.month + 1).toString());
        }
        if (values.pay_period) {
          formData.append("pay_period", values.pay_period);
        }
        if (values.file) {
          formData.append("file", values.file);
        }
        logger.debug({
          year: values.mp?.year,
          month: values.mp ? values.mp.month + 1 : undefined,
          pay_period: values.pay_period,
          file: values.file,
        });
        console.log("Making form data submission request with config:", config);
        response = await client.post(
          `${apiConfig.endpoint}`,
          formData,
          config
        );
      } else {
        const params: Record<string, any> = {
          month: values.date
            ? (values.date.getUTCMonth() + 1).toString()
            : values.mp
            ? (values.mp.month + 1).toString()
            : undefined,
          year: values.date
            ? values.date.getUTCFullYear().toString()
            : values.mp
            ? values.mp.year.toString()
            : undefined,
        };

        if (values.date) {
          params.day = values.date.getUTCDate().toString();
        } else if (
          values.pay_period !== undefined &&
          values.pay_period !== null
        ) {
          params.day = values.pay_period;
        }

        if (apiConfig.params) {
          Object.assign(params, apiConfig.params);
        }
        console.log("Making request with config:", config);
        console.log("Request params:", params);
        logger.debug(new URLSearchParams(params).toString());
        response = await client.post(
          `${apiConfig.endpoint}?${new URLSearchParams(params)}`,
          "",
          config
        );
      }

      console.log("Response headers received:", response.headers);

      const contentType = response.headers["content-type"];
      if (contentType === "application/json") {
        logger.debug(response.data);
      } else {
        logger.debug(response.headers);
        const disposition = response.headers["content-disposition"];
        const filename = disposition.split(";")[1].split("filename=")[1].trim();

        const file = new Blob([response.data], { type: contentType });
        const url = window.URL.createObjectURL(file);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
      }

      apiConfig.onResponse?.(response);
    } catch (err) {
      const e = err as AxiosError;
      setError(e);
      logger.debug(values);
      throw e;
    }
  };

  const nhandleSubmit = async (values: T) => {
    try {
      await submitForm(values);
      await onSubmit(values);
    } catch (error) {
      if (error instanceof AxiosError) {
        setError(error);
      }
      throw error;
    }
  };

  return {
    handleSubmit: handleSubmit(nhandleSubmit),
    register,
    errors,
    isSubmitting,
    isSubmitSuccessful,
    error,
    setValue,
    watch,
  };
};
