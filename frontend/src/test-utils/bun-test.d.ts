// Extend Bun's expect with jest-dom matchers
import "@testing-library/jest-dom";

declare module "bun:test" {
  interface Matchers<R = unknown> {
    toBeInTheDocument(): R;
    toHaveAttribute(attr: string, value?: string): R;
    toBeVisible(): R;
    toBeDisabled(): R;
    toBeEnabled(): R;
    toHaveTextContent(text: string | RegExp): R;
    toHaveValue(value: string | string[] | number): R;
    toHaveClass(...classNames: string[]): R;
    toHaveStyle(style: Record<string, unknown>): R;
    toHaveFocus(): R;
    toBeChecked(): R;
    toBeEmpty(): R;
    toContainElement(element: HTMLElement | null): R;
    toContainHTML(html: string): R;
    toHaveAccessibleDescription(description?: string | RegExp): R;
    toHaveAccessibleName(name?: string | RegExp): R;
    toHaveDisplayValue(value: string | RegExp | Array<string | RegExp>): R;
    toHaveFormValues(values: Record<string, unknown>): R;
    toBeInvalid(): R;
    toBeRequired(): R;
    toBeValid(): R;
    toHaveErrorMessage(message?: string | RegExp): R;
  }
}
