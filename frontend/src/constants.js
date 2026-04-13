/** Note values shown in the form; must match backend ACCEPTED_DENOMINATIONS order for display. */
export const DENOMINATION_ORDER = ["500", "50", "20", "10", "5", "2", "1"];

/** Initial empty counts for denomination inputs. */
export function emptyDenominations() {
  return {
    "500": "",
    "50": "",
    "20": "",
    "10": "",
    "5": "",
    "2": "",
    "1": "",
  };
}
