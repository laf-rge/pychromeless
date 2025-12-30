type LogLevel = "debug" | "info" | "warn" | "error";

class Logger {
  private log(level: LogLevel, ...args: unknown[]): void {
    if (import.meta.env.DEV) {
      const method = level === "debug" ? "log" : level;
      console[method](`[${level.toUpperCase()}]`, ...args);
    }
  }

  debug(...args: unknown[]): void {
    this.log("debug", ...args);
  }

  info(...args: unknown[]): void {
    this.log("info", ...args);
  }

  warn(...args: unknown[]): void {
    this.log("warn", ...args);
  }

  error(...args: unknown[]): void {
    this.log("error", ...args);
  }
}

export const logger = new Logger();
