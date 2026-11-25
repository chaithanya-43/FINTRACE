export const FRAUD_CATEGORIES = [
  ["upi_fraud", "UPI fraud"],
  ["card_fraud", "Card fraud"],
  ["net_banking_fraud", "Net banking fraud"],
  ["investment_fraud", "Investment fraud"],
  ["loan_app_fraud", "Loan app fraud"],
  ["job_offer_fraud", "Job offer fraud"],
  ["otp_phishing", "OTP phishing"],
  ["sextortion", "Sextortion"],
  ["sim_swap", "SIM swap"],
  ["impersonation", "Impersonation"],
  ["merchant_fraud", "Merchant fraud"],
  ["unknown", "Not sure"],
];

export const FRAUD_CHANNELS = [
  ["upi", "UPI"],
  ["card", "Card"],
  ["net_banking", "Net banking"],
  ["whatsapp", "WhatsApp"],
  ["phone_call", "Phone call"],
  ["sms", "SMS"],
  ["email", "Email"],
  ["social_media", "Social media"],
  ["mobile_app", "Mobile app"],
  ["in_person", "In person"],
  ["unknown", "Not sure"],
];

export const COMPLAINT_CHANNELS = [
  ["cybercrime_portal", "Cybercrime portal"],
  ["bank", "Bank"],
  ["nodal_officer", "Nodal officer"],
  ["police_station", "Police station"],
  ["rbi_ombudsman", "RBI ombudsman"],
  ["other", "Other"],
];

export const SUBMISSION_STATUSES = [
  ["draft", "Draft"],
  ["ready", "Ready to submit"],
  ["submitted", "Submitted"],
  ["acknowledged", "Acknowledged"],
  ["rejected", "Rejected"],
  ["withdrawn", "Withdrawn"],
];

export const RECOVERY_STATUSES = [
  ["pending", "Pending"],
  ["in_progress", "In progress"],
  ["completed", "Completed"],
  ["skipped", "Skipped"],
  ["blocked", "Blocked"],
];

export const OUTCOME_STATUSES = [
  ["unknown", "Not recorded"],
  ["pending", "Pending"],
  ["recovered", "Recovered"],
  ["partially_recovered", "Partially recovered"],
  ["not_recovered", "Not recovered"],
];

export const CASE_STATUSES = [
  ["intake", "Intake"],
  ["collecting_evidence", "Collecting evidence"],
  ["assessment", "Assessment"],
  ["recovery", "Recovery"],
  ["closed", "Closed"],
];

export const AUTHORIZATION_TYPES = [
  ["unauthorized", "I did not authorise it"],
  ["authorized_deceived", "I approved it but was deceived"],
  ["unknown", "Not sure"],
];

export function labelFor(pairs, value) {
  const match = pairs.find(([key]) => key === value);
  if (!match) {
    return value ? String(value).replaceAll("_", " ") : "—";
  }
  return match[1];
}

export function formatMoney(amount, currency = "INR") {
  if (amount === null || amount === undefined || amount === "") {
    return "—";
  }
  const numeric = Number(amount);
  if (Number.isNaN(numeric)) {
    return String(amount);
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(numeric);
}

export function formatDateTime(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function formatDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleDateString("en-IN", { dateStyle: "medium" });
}
