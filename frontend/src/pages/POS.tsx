/**
 * BTCPay Server Point of Sale page.
 * Unauthenticated, standalone page for employee iPad use.
 * Not linked from anywhere in the app - accessed directly via /pos.
 */
export function POS() {
  return (
    <div className="flex flex-col landscape:flex-row h-screen w-screen bg-gray-950 text-gray-100">
      {/* Directions panel - top in portrait, left in landscape */}
      <div className="landscape:w-1/3 portrait:h-[40%] flex flex-col p-4 landscape:p-6 overflow-y-auto landscape:border-r portrait:border-b border-gray-800">
        <h1 className="text-xl landscape:text-2xl font-bold mb-3 landscape:mb-6">
          Bitcoin Payments
        </h1>

        {/* Portrait: two-column grid (steps left, good-to-know right). Landscape: single column. */}
        <div className="portrait:grid portrait:grid-cols-[1fr_auto] portrait:gap-x-6 landscape:space-y-4 text-xs landscape:text-sm leading-relaxed">
          {/* Steps + payment failed - left column in portrait */}
          <div className="portrait:space-y-1.5 landscape:space-y-4">
            <section>
              <h2 className="text-base landscape:text-lg font-semibold text-green-400 mb-2 landscape:mb-3">
                Steps
              </h2>
              <ol className="list-decimal list-inside space-y-1.5 landscape:space-y-3 text-gray-300">
                <li>
                  Ring up the customer's items in the{" "}
                  <strong className="text-white">POS as normal</strong>.
                </li>
                <li>
                  Ask if they are a{" "}
                  <strong className="text-white">Shore Points member</strong>.
                </li>
                <li>
                  Go to the <strong className="text-white">payment screen</strong>.
                </li>
                <li>
                  Select{" "}
                  <strong className="text-white">House Account</strong>.
                </li>
                <li>
                  Type{" "}
                  <strong className="text-white">bitcoin</strong>{" "}
                  as the house account name.
                </li>
                <li>
                  Enter the <strong className="text-white">order total</strong>{" "}
                  on the keypad{" "}
                  <span className="hidden landscape:inline">to the right</span>
                  <span className="landscape:hidden">below</span>.
                </li>
                <li>
                  Tap{" "}
                  <strong className="text-white">Charge</strong>{" "}
                  to generate a QR code.
                </li>
                <li>
                  Have the customer{" "}
                  <strong className="text-white">scan the QR code</strong> with
                  their Bitcoin Lightning wallet.
                </li>
                <li>
                  Wait for the screen to show the payment is{" "}
                  <strong className="text-green-400">settled</strong>.
                  Lightning payments confirm instantly.
                </li>
                <li>
                  Press <strong className="text-white">Pay</strong> on the POS.
                </li>
              </ol>
            </section>

            <p className="text-red-400 text-xs mt-2">
              <strong>Payment failed?</strong>{" "}
              <span className="text-gray-400">Ask for a different payment method &mdash; you're already on the payment screen.</span>
            </p>
          </div>

          {/* Good to Know - right column in portrait, below steps in landscape */}
          <section className="p-3 landscape:p-4 rounded-lg bg-gray-900 border border-gray-700 portrait:w-48 portrait:self-start portrait:mt-6">
            <h3 className="font-semibold text-yellow-400 mb-2">Good to Know</h3>
            <ul className="list-disc list-inside space-y-1.5 landscape:space-y-2 text-gray-300">
              <li>
                We <strong className="text-white">do not</strong> support tips
                via Bitcoin. If a customer wants to tip, let them know they can
                leave a <strong className="text-white">cash tip</strong>.
              </li>
              <li>
                The QR code expires after a few minutes. Tap the back arrow and
                re-enter the amount to generate a new one.
              </li>
              <li>If the keypad doesn't load, refresh the page.</li>
            </ul>
          </section>
        </div>
      </div>

      {/* BTCPay Server iframe - bottom in portrait, right in landscape */}
      <div className="flex-1 flex min-h-0">
        <iframe
          src="https://pay.wagonermanagement.com/apps/EZKuygrmpdH69jT9eZ1PZ6qhoq6/pos"
          className="w-full h-full border-0"
          title="BTCPay Point of Sale"
          allow="payment"
        />
      </div>
    </div>
  );
}
