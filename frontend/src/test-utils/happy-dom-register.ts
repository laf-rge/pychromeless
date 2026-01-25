// This file MUST be loaded before any other test setup files
// It registers happy-dom globals (window, document, etc.)
// No other imports allowed here to ensure happy-dom is registered first
import { GlobalRegistrator } from "@happy-dom/global-registrator";

GlobalRegistrator.register();
