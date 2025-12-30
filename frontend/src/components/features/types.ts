import { UseFormRegister, UseFormSetValue } from "react-hook-form";
import { AxiosResponse } from "axios";

export interface MonthPickerValue {
  month: number;
  year: number;
}

export interface FormValues {
  date?: Date;
  mp?: MonthPickerValue;
  pay_period?: string;
  file?: File;
  invoiceNumber?: string;
  locations?: string[];
}

export interface ApiConfig {
  baseURL: string;
  endpoint: string;
  params?: Record<string, any>;
  formDataSubmission: boolean;
  defaultValues?: Partial<FormValues>;
  onResponse?: (response: AxiosResponse) => void;
}

export interface ValidationRules {
  mp?: Record<string, (value: any) => boolean | string>;
  pay_period?: Record<string, (value: any) => boolean | string>;
}

export interface DateAndPayPeriodProps {
  register: UseFormRegister<FormValues>;
  setValue: UseFormSetValue<FormValues>;
  errors: any;
  validate?: ValidationRules;
}
