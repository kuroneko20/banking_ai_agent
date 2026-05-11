"""
Static policy / FAQ data for the Banking AI-Agent.
In production this would be stored in a database or vector store.
"""

from __future__ import annotations

from app.core.schemas import Intent

# ---------------------------------------------------------------------------
# Policy records keyed by intent
# ---------------------------------------------------------------------------

POLICIES: dict[str, dict[str, str]] = {
    Intent.TRANSFER_FAILED: {
        "faq": (
            "Transfers can fail due to: incorrect beneficiary details, "
            "insufficient funds, daily transfer limit exceeded, or temporary "
            "system issues. Processing usually takes up to 3 business days."
        ),
        "resolution_guideline": (
            "1. Confirm the transfer status in the transaction history. "
            "2. Verify the beneficiary account number and bank code. "
            "3. Check the customer's available balance and daily limits. "
            "4. If the issue persists after 3 business days, initiate a trace "
            "request (reference number required). "
            "5. Refund is automatically triggered within 7 business days if "
            "the transfer cannot be completed."
        ),
        "escalation_condition": (
            "Escalate if: the amount > $5,000, customer reports fraud, "
            "trace request exceeds 7 business days, or the transaction is "
            "marked as suspicious."
        ),
    },
    Intent.REFUND_REQUEST: {
        "faq": (
            "Refunds are processed within 3–7 business days depending on the "
            "payment method. Debit card refunds may take up to 10 business days."
        ),
        "resolution_guideline": (
            "1. Verify the original transaction details (date, amount, merchant). "
            "2. Confirm the refund eligibility period (within 30 days). "
            "3. Submit a refund request with the transaction reference. "
            "4. Notify the customer of the expected timeline. "
            "5. Follow up after 7 days if refund not received."
        ),
        "escalation_condition": (
            "Escalate if: refund not received after 10 business days, "
            "customer disputes the eligibility, or amount > $1,000."
        ),
    },
    Intent.BLOCKED_ACCOUNT: {
        "faq": (
            "Accounts are blocked due to: multiple failed login attempts, "
            "suspicious activity detected, regulatory compliance hold, "
            "or customer request. A blocked account cannot make transactions."
        ),
        "resolution_guideline": (
            "1. Verify the customer's identity with KYC documents. "
            "2. Determine the reason for the block (system notes). "
            "3. If blocked due to failed logins: reset credentials and unblock. "
            "4. If blocked due to suspicious activity: compliance review required. "
            "5. Inform the customer of the expected resolution timeline (24–72 hrs)."
        ),
        "escalation_condition": (
            "Escalate immediately if: block is due to suspected fraud, "
            "AML/compliance hold, or customer cannot verify identity."
        ),
    },
    Intent.LOST_CARD: {
        "faq": (
            "A lost or stolen card should be reported immediately. "
            "The card will be blocked within minutes of the report. "
            "A replacement card is issued within 5–7 business days."
        ),
        "resolution_guideline": (
            "1. Block the card immediately via the card management system. "
            "2. Record the loss report with date and time. "
            "3. Initiate a replacement card order. "
            "4. Advise the customer to monitor their account for unauthorized charges. "
            "5. Offer a temporary virtual card if available."
        ),
        "escalation_condition": (
            "Escalate if: unauthorized transactions detected after card loss, "
            "or customer suspects card theft (police report may be required)."
        ),
    },
    Intent.CARD_NOT_RECEIVED: {
        "faq": (
            "New or replacement cards are delivered within 7–10 business days. "
            "Express delivery is available for an additional fee."
        ),
        "resolution_guideline": (
            "1. Confirm the card dispatch date and delivery address. "
            "2. Check the courier tracking status. "
            "3. If past the expected delivery window, cancel the card and reissue. "
            "4. Verify mailing address with the customer before reissuing."
        ),
        "escalation_condition": (
            "Escalate if: address discrepancy found, potential mail fraud suspected, "
            "or second reissuance request."
        ),
    },
    Intent.SUSPICIOUS_TRANSACTION: {
        "faq": (
            "Suspicious transactions are flagged by our fraud detection system "
            "or reported by the customer. Immediate action protects the account."
        ),
        "resolution_guideline": (
            "1. Immediately place a temporary hold on the account if required. "
            "2. Gather transaction details: amount, merchant, date, location. "
            "3. Ask the customer to confirm if they recognise the transaction. "
            "4. If unrecognised, initiate a fraud dispute and block the card. "
            "5. File a chargeback request with the relevant payment network. "
            "6. Notify the fraud team for investigation."
        ),
        "escalation_condition": (
            "Escalate immediately to the fraud team. This is always a HIGH priority case."
        ),
    },
    Intent.ACCOUNT_BALANCE: {
        "faq": (
            "Account balance includes available balance and pending transactions. "
            "Balances are updated in real-time for most transaction types."
        ),
        "resolution_guideline": (
            "1. Advise the customer to check the mobile app or internet banking. "
            "2. Explain the difference between available balance and current balance. "
            "3. Clarify pending transaction holds if applicable."
        ),
        "escalation_condition": (
            "Escalate if: balance discrepancy > $100 that cannot be explained "
            "by pending transactions."
        ),
    },
    Intent.LOAN_SUPPORT: {
        "faq": (
            "Personal loans, home loans, and auto loans are available. "
            "Loan enquiries require income verification and credit assessment. "
            "Approval typically takes 2–5 business days."
        ),
        "resolution_guideline": (
            "1. Identify the loan type the customer is enquiring about. "
            "2. Provide applicable interest rates and repayment terms. "
            "3. Direct the customer to the loan application portal. "
            "4. Request supporting documents: payslips, ID, bank statements."
        ),
        "escalation_condition": (
            "Escalate to the loans team if: customer has a complex financial situation "
            "or requires a loan officer consultation."
        ),
    },
    Intent.PASSWORD_RESET: {
        "faq": (
            "Passwords can be reset via the mobile app, internet banking, "
            "or by calling the support line. Reset links expire in 15 minutes."
        ),
        "resolution_guideline": (
            "1. Direct the customer to the 'Forgot Password' link on the login page. "
            "2. Verify the registered email or mobile number for OTP delivery. "
            "3. If OTP not received, check spam folder or try alternative channel. "
            "4. For persistent issues, perform manual identity verification and reset."
        ),
        "escalation_condition": (
            "Escalate if: customer cannot access registered email/phone, "
            "or if suspicious login attempts are detected."
        ),
    },
    Intent.LOGIN_ISSUE: {
        "faq": (
            "Login issues can be caused by incorrect credentials, expired passwords, "
            "browser cache, or account lock after multiple failed attempts."
        ),
        "resolution_guideline": (
            "1. Ask if the customer is using the correct username/email. "
            "2. Check if the account is locked (failed attempt counter). "
            "3. Suggest clearing browser cache or using a different browser. "
            "4. Offer password reset if the password is forgotten. "
            "5. Unlock the account after verifying identity."
        ),
        "escalation_condition": (
            "Escalate if: account was locked due to suspected intrusion or "
            "customer reports they never attempted to log in."
        ),
    },
    Intent.GENERAL_INQUIRY: {
        "faq": (
            "We offer a full range of banking services including savings accounts, "
            "credit cards, loans, investments, and digital banking."
        ),
        "resolution_guideline": (
            "1. Understand the customer's specific inquiry. "
            "2. Provide relevant product or service information. "
            "3. Direct to the appropriate page or department if needed."
        ),
        "escalation_condition": (
            "Escalate if the inquiry requires specialist knowledge or involves "
            "regulatory/legal matters."
        ),
    },
    Intent.UNKNOWN: {
        "faq": "We are here to help with all banking-related enquiries.",
        "resolution_guideline": (
            "1. Ask the customer to clarify their request. "
            "2. Offer a list of common topics we can assist with."
        ),
        "escalation_condition": "Escalate if the customer seems distressed or the inquiry is unclear after two attempts.",
    },
}


def get_policy(intent: Intent) -> dict[str, str]:
    """Return the policy record for the given intent.

    Falls back to GENERAL_INQUIRY if the intent has no dedicated policy.
    """
    return POLICIES.get(intent, POLICIES[Intent.GENERAL_INQUIRY])
