import { describe, expect, it } from "vitest";

import {
  COMPLAINT_CHANNELS,
  formatDate,
  formatDateTime,
  formatMoney,
  labelFor,
} from "./constants";

describe("labelFor", () => {
  it("returns the human label for a known value", () => {
    expect(labelFor(COMPLAINT_CHANNELS, "cybercrime_portal")).toBe("Cybercrime portal");
  });

  it("humanises an unknown value instead of hiding it", () => {
    expect(labelFor(COMPLAINT_CHANNELS, "some_new_channel")).toBe("some new channel");
  });

  it("renders a dash for an empty value", () => {
    expect(labelFor(COMPLAINT_CHANNELS, null)).toBe("—");
  });
});

describe("formatMoney", () => {
  it("formats a numeric string as INR", () => {
    expect(formatMoney("15000")).toContain("15,000");
  });

  it("returns a dash when no amount is recorded", () => {
    expect(formatMoney(null)).toBe("—");
  });
});

describe("date helpers", () => {
  it("returns a dash for missing values", () => {
    expect(formatDate(undefined)).toBe("—");
    expect(formatDateTime(null)).toBe("—");
  });
});
