import React, { useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";

import InvoiceDetails from "./components/InvoiceDetails";
import PurchaseHistoryTable from "./components/PurchaseHistoryTable";
import {
  DENOMINATION_ORDER,
  emptyDenominations,
} from "./constants";

/**
 * Backend base URL from frontend/.env
 * Example:
 * REACT_APP_BACKEND_URL=http://localhost:8000
 */
const BackendUrl =
  process.env.REACT_APP_BACKEND_URL?.trim() || "";

/**
 * Convert nested DRF validation errors into plain lines for alert().
 */
function collectValidationMessages(data, prefix = "") {
  const out = [];

  if (data == null) return out;

  if (typeof data === "string") {
    out.push(prefix ? `${prefix}: ${data}` : data);
    return out;
  }

  if (Array.isArray(data)) {
    data.forEach((item, index) => {
      const label = prefix
        ? `${prefix}[${index + 1}]`
        : `[${index + 1}]`;

      out.push(
        ...collectValidationMessages(item, label)
      );
    });

    return out;
  }

  if (typeof data === "object") {
    if (data.detail != null) {
      out.push(
        ...collectValidationMessages(
          data.detail,
          prefix
        )
      );
    }

    for (const [key, value] of Object.entries(data)) {
      if (
        key === "detail" ||
        key === "required" ||
        key === "received"
      ) {
        continue;
      }

      const label = prefix ? `${prefix}.${key}` : key;

      if (key === "error") {
        const req =
          data.required != null
            ? ` (required: ${data.required})`
            : "";

        const recv =
          data.received != null
            ? ` (received: ${data.received})`
            : "";

        out.push(`${value}${req}${recv}`);
        continue;
      }

      if (
        Array.isArray(value) &&
        value.every((x) => typeof x === "string")
      ) {
        value.forEach((msg) =>
          out.push(`${label}: ${msg}`)
        );
      } else if (
        value != null &&
        typeof value === "object"
      ) {
        out.push(
          ...collectValidationMessages(
            value,
            label
          )
        );
      } else if (value != null) {
        out.push(`${label}: ${value}`);
      }
    }
  }

  return out;
}

/**
 * Convert axios / network errors into readable messages.
 */
function messagesFromAxiosError(error, backendUrl) {
  if (!backendUrl) {
    return [
      "Set REACT_APP_BACKEND_URL in frontend/.env.",
    ];
  }

  const status = error?.response?.status;
  const data = error?.response?.data;

  if (data) {
    const lines = collectValidationMessages(data);
    if (lines.length) return lines;
  }

  if (error?.code === "ECONNABORTED") {
    return ["Request timed out. Try again."];
  }

  if (error?.message === "Network Error") {
    return [
      "Cannot reach backend. Check server and .env URL.",
    ];
  }

  if (status === 404) return ["Not found."];
  if (status >= 500)
    return ["Server error. Try again later."];

  return [
    error?.message || "Request failed.",
  ];
}

/**
 * Quick frontend validation.
 * Backend still performs final validation.
 */
function validateBillForm({
  customerEmail,
  products,
  amountPaid,
}) {
  const errors = [];

  const email = customerEmail.trim();

  if (!email) {
    errors.push("Customer email is required.");
  } else if (
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  ) {
    errors.push("Enter a valid email.");
  }

  const rows = products.filter(
    (row) =>
      row.product_id.trim() ||
      String(row.quantity).trim()
  );

  if (!rows.length) {
    errors.push(
      "Add at least one product row."
    );
  }

  rows.forEach((row, index) => {
    const line = `Line ${index + 1}`;

    if (!row.product_id.trim()) {
      errors.push(
        `${line}: Product ID required.`
      );
    }

    const qty = Number(row.quantity);

    if (!Number.isInteger(qty) || qty < 1) {
      errors.push(
        `${line}: Quantity must be at least 1.`
      );
    }
  });

  if (amountPaid === "") {
    errors.push("Cash paid is required.");
  } else {
    const paid = Number(amountPaid);

    if (!Number.isFinite(paid) || paid < 0) {
      errors.push(
        "Cash paid must be valid."
      );
    }
  }

  return errors;
}

export default function App() {
  const [customerEmail, setCustomerEmail] =
    useState("");

  const [products, setProducts] = useState([
    { product_id: "", quantity: "" },
  ]);

  const [denominations, setDenominations] =
    useState(emptyDenominations());

  const [amountPaid, setAmountPaid] =
    useState("");

  const [billResult, setBillResult] =
    useState(null);

  const [purchaseHistory, setPurchaseHistory] =
    useState([]);

  const [submitting, setSubmitting] =
    useState(false);

  /** Add new product row */
  const addRow = () => {
    setProducts((prev) => [
      ...prev,
      { product_id: "", quantity: "" },
    ]);
  };

  /** Update one product row field */
  const handleProductChange = (
    index,
    field,
    value
  ) => {
    setProducts((prev) => {
      const next = [...prev];
      next[index] = {
        ...next[index],
        [field]: value,
      };
      return next;
    });
  };

  /** Update denomination count */
  const handleDenominationChange = (
    note,
    value
  ) => {
    setDenominations((prev) => ({
      ...prev,
      [note]: value,
    }));
  };

  /** Load previous bills for email */
  const fetchPurchases = async (email) => {
    if (!email.trim() || !BackendUrl) {
      setPurchaseHistory([]);
      return;
    }

    try {
      const response = await axios.get(
        `${BackendUrl}/bills/customer/${encodeURIComponent(
          email
        )}/`,
        { timeout: 10000 }
      );

      setPurchaseHistory(response.data || []);
    } catch {
      setPurchaseHistory([]);
    }
  };

  const handleEmailChange = (value) => {
    setCustomerEmail(value);
    fetchPurchases(value);
  };

  /** Submit bill */
  const handleSubmit = async () => {
    if (submitting) return;

    const errors = validateBillForm({
      customerEmail,
      products,
      amountPaid,
    });

    if (errors.length) {
      alert(errors.join("\n"));
      return;
    }

    if (!BackendUrl) {
      alert(
        "Set REACT_APP_BACKEND_URL in .env and restart npm."
      );
      return;
    }

    const payload = {
      customer_email: customerEmail.trim(),

      products_list: products
        .filter(
          (row) =>
            row.product_id.trim() ||
            String(row.quantity).trim()
        )
        .map((row) => ({
          product_id: row.product_id.trim(),
          quantity: Number(row.quantity),
        })),

      amount_paid: Number(amountPaid),

      denominations: Object.fromEntries(
        Object.entries(denominations).map(
          ([note, count]) => [
            note,
            Number(count || 0),
          ]
        )
      ),
    };

    setSubmitting(true);

    try {
      const response = await axios.post(
        `${BackendUrl}/generate-bill/`,
        payload,
        { timeout: 15000 }
      );

      setBillResult(response.data || null);

      // Do not block submit completion on history refresh.
      fetchPurchases(customerEmail);

      setCustomerEmail("");
      setProducts([
        { product_id: "", quantity: "" },
      ]);
      setDenominations(
        emptyDenominations()
      );
      setAmountPaid("");

      alert(
        `Bill generated. Invoice ${response.data.invoice_id}.`
      );
    } catch (error) {
      alert(
        messagesFromAxiosError(
          error,
          BackendUrl
        ).join("\n")
      );
    } finally {
      setSubmitting(false);
    }
  };

  /** Open saved invoice */
  const openInvoice = async (invoiceId) => {
    if (!BackendUrl) {
      alert("Set backend URL in .env.");
      return;
    }

    if (!invoiceId) {
      alert("Invalid invoice.");
      return;
    }

    try {
      const response = await axios.get(
        `${BackendUrl}/bills/${invoiceId}/`
      );

      setBillResult(response.data || null);
    } catch (error) {
      alert(
        messagesFromAxiosError(
          error,
          BackendUrl
        ).join("\n")
      );
    }
  };

  /** Reset form only */
  const handleCancel = () => {
    setProducts([
      { product_id: "", quantity: "" },
    ]);
    setDenominations(
      emptyDenominations()
    );
    setAmountPaid("");
    setBillResult(null);
  };

  return (
    <div className="container mt-4 mb-5">
      <div className="border p-4">
        <h4 className="text-center mb-4">
          Billing Page
        </h4>

        {/* Customer Email */}
        <div className="row mb-4">
          <label className="col-sm-3 col-form-label">
            Customer Email
          </label>

          <div className="col-sm-5">
            <input
              type="email"
              className="form-control"
              value={customerEmail}
              placeholder="Enter email"
              autoComplete="email"
              onChange={(e) =>
                handleEmailChange(
                  e.target.value
                )
              }
            />
          </div>
        </div>

        {/* Products */}
        <div className="mb-3">
          <div className="d-flex justify-content-between mb-2">
            <strong>Bill Section</strong>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={addRow}
            >
              Add New
            </button>
          </div>

          {products.map((item, index) => (
            <div
              className="row mb-2"
              key={index}
            >
              <div className="col-sm-4">
                <input
                  className="form-control"
                  placeholder="Product ID"
                  value={item.product_id}
                  onChange={(e) =>
                    handleProductChange(
                      index,
                      "product_id",
                      e.target.value
                    )
                  }
                />
              </div>

              <div className="col-sm-3">
                <input
                  className="form-control"
                  type="number"
                  min={1}
                  step={1}
                  placeholder="Quantity"
                  value={item.quantity}
                  onChange={(e) =>
                    handleProductChange(
                      index,
                      "quantity",
                      e.target.value
                    )
                  }
                />
              </div>
            </div>
          ))}
        </div>

        {/* Denominations */}
        <hr />

        <div className="mb-4">
          <strong>Denominations</strong>

          {DENOMINATION_ORDER.map((note) => (
            <div
              className="row mt-2"
              key={note}
            >
              <div className="col-sm-2">
                {note}
              </div>

              <div className="col-sm-3">
                <input
                  className="form-control"
                  placeholder="Count"
                  value={
                    denominations[note]
                  }
                  onChange={(e) =>
                    handleDenominationChange(
                      note,
                      e.target.value
                    )
                  }
                />
              </div>
            </div>
          ))}
        </div>

        {/* Payment */}
        <div className="row mb-4">
          <label className="col-sm-3 col-form-label">
            Cash Paid
          </label>

          <div className="col-sm-4">
            <input
              className="form-control"
              type="number"
              min={0}
              step="0.01"
              value={amountPaid}
              onChange={(e) =>
                setAmountPaid(
                  e.target.value
                )
              }
            />
          </div>
        </div>

        {/* Actions */}
        <div className="text-end">
          <button
            type="button"
            className="btn btn-outline-secondary me-2"
            onClick={handleCancel}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            type="button"
            className="btn btn-success"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting
              ? "Generating..."
              : "Generate Bill"}
          </button>
        </div>

        {/* Current Invoice */}
        {billResult && (
          <InvoiceDetails bill={billResult} />
        )}

        {/* Previous Purchases */}
        <PurchaseHistoryTable
          rows={purchaseHistory}
          onView={openInvoice}
        />
      </div>
    </div>
  );
}