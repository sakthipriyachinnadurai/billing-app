import React from "react";

/**
 * Shows previous customer purchases.
 * Clicking View loads full invoice details.
 */
export default function PurchaseHistoryTable({
  rows = [],
  onView,
}) {
  /**
   * Format money values safely.
   */
  const money = (value) => {
    if (
      value === "" ||
      value === null ||
      value === undefined
    ) {
      return "-";
    }

    const num = Number(
      String(value).replace(/,/g, "")
    );

    if (Number.isNaN(num)) {
      return String(value);
    }

    return `Rs. ${num.toFixed(2)}`;
  };

  /**
   * Format date/time safely.
   */
  const formatDate = (value) => {
    if (!value) return "-";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return (
      date.toLocaleString("en-IN", {
        timeZone: "UTC",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }) + " UTC"
    );
  };

  const list = Array.isArray(rows) ? rows : [];
  const hasRows = list.length > 0;

  return (
    <>
      <hr className="my-5" />

      <h5>Previous Purchases</h5>

      <table className="table table-bordered">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Total</th>
            <th>Paid</th>
            <th>Balance</th>
            <th>Date</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {hasRows ? (
            list.map((row, index) => {
              const invoiceId =
                row.invoice_id || `row-${index}`;

              return (
                <tr key={invoiceId}>
                  <td>{row.invoice_id || "-"}</td>
                  <td>{money(row.total_amount)}</td>
                  <td>{money(row.amount_paid)}</td>
                  <td>{money(row.balance_amount)}</td>
                  <td>
                    {formatDate(
                      row.transaction_time
                    )}
                  </td>

                  <td>
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() =>
                        onView &&
                        onView(row.invoice_id)
                      }
                    >
                      View
                    </button>
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td
                colSpan={6}
                className="text-center text-muted"
              >
                No purchases found. Type a customer
                email to load history, or generate a
                bill first.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}