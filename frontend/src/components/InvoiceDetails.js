import React from "react";

/**
 * Displays one generated invoice / saved bill.
 * Expects `bill` object from API response.
 */
export default function InvoiceDetails({ bill }) {
  // Nothing selected yet
  if (!bill) return null;

  /**
   * Format numbers as currency with 2 decimals.
   * Handles null / empty / invalid values safely.
   */
  const money = (value) => {
    if (value === "" || value === null || value === undefined) {
      return "-";
    }

    const num = Number(String(value).replace(/,/g, ""));
    return Number.isNaN(num) ? String(value) : num.toFixed(2);
  };

  /**
   * Format transaction date.
   * If invalid date received, show raw value.
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

  const lines = bill.products_list || [];
  const change = bill.change_breakdown || {};
  const showChange = Object.keys(change).length > 0;

  return (
    <>
      <hr className="my-5" />

      <h4 className="text-center mb-4">Invoice Details</h4>

      {/* Header Details */}
      <p>
        <strong>Invoice ID:</strong> {bill.invoice_id}
      </p>

      <p>
        <strong>Email:</strong> {bill.customer_email}
      </p>

      <p>
        <strong>Date:</strong> {formatDate(bill.transaction_time)}
      </p>

      {/* Product Line Items */}
      <table className="table table-bordered mt-4">
        <thead>
          <tr>
            <th>Product ID</th>
            <th>Unit Price</th>
            <th>Qty</th>
            <th>Tax %</th>
            <th>Tax Amount</th>
            <th>Total</th>
          </tr>
        </thead>

        <tbody>
          {lines.map((item, index) => (
            <tr key={`${item.product_id}-${index}`}>
              <td>{item.product_id}</td>
              <td>Rs. {money(item.unit_price)}</td>
              <td>{item.quantity}</td>
              <td>{money(item.tax_rate)}%</td>
              <td>Rs. {money(item.tax_amount)}</td>
              <td>Rs. {money(item.total_price)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Totals */}
      <div className="text-end">
        <p>
          <strong>Subtotal:</strong> Rs. {money(bill.subtotal)}
        </p>

        <p>
          <strong>Total Tax:</strong> Rs. {money(bill.total_tax)}
        </p>

        <p>
          <strong>Total:</strong> Rs. {money(bill.total_amount)}
        </p>

        <p>
          <strong>Paid:</strong> Rs. {money(bill.amount_paid)}
        </p>

        <p>
          <strong>Balance:</strong> Rs. {money(bill.balance_amount)}
        </p>
      </div>

      {/* Change Breakdown */}
      {showChange && (
        <>
          <hr />

          <h5>Balance Denomination</h5>

          <table className="table table-bordered w-50">
            <thead>
              <tr>
                <th>Note</th>
                <th>Count</th>
              </tr>
            </thead>

            <tbody>
              {Object.entries(change).map(([note, count]) => (
                <tr key={note}>
                  <td>Rs. {note}</td>
                  <td>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}