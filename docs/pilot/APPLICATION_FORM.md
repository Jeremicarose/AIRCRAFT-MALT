# Pilot Application Form

This is the form-ready application for the CKB Receiver Registry pilot. Build it
in a form service that supports branching and access-controlled responses. Keep
contact information outside the public repository.

## Form Introduction

Thank you for your interest in testing CKB Receiver Registry, an experimental
browser tool for managing persistent ADS-B and Mode S receiver identities.

The pilot includes a remote product test of up to 45 minutes, an interview of up
to 20 minutes, and a short follow-up within seven days. Receiver operators should
expect about 85-95 minutes total. Coordinators should expect about 90-120 minutes
total, including a small integration review.

Testing uses CKB Pudge testnet. No real funds or physical receiver connection are
required. We will never ask for private keys, seed phrases, passwords, feed keys,
private feed URLs, IP addresses, or exact receiver locations.

Completing this form expresses interest. It is not consent to participate and
does not guarantee selection. We will contact selected applicants with the full
study information and a separate consent form before scheduling.

The proposed $30 USD-equivalent completion incentive is conditional on grant
approval and is not currently guaranteed.

Estimated completion time: 5-8 minutes.

## Questions For Everyone

1. **Name or public handle**

   Short answer. Required.

2. **Email address or preferred contact method**

   Short answer. Required. State that this will be stored privately and used only
   for pilot recruitment and scheduling.

3. **Which role best describes you?**

   Single choice. Required.
   - Receiver owner or operator
   - Receiver-network coordinator
   - Developer or maintainer of receiver-network software
   - Other relevant role: [short answer]

4. **Which receiver networks, projects, or communities are you involved with?**

   Long answer. Required. Ask only for non-sensitive information.

5. **What time zone are you in? You may include your country if you choose.**

   Short answer. Required. Add: "Do not provide a home address or receiver
   location."

6. **Which general time windows are suitable for a remote session?**

   Checkbox grid or long answer. Required. Show times in the maintainer's stated
   scheduling time zone.

7. **Can you join a remote call using a laptop or desktop, current
   Chromium-based browser, microphone, and stable internet suitable for screen
   sharing?**

   Single choice. Required.
   - Yes
   - Yes, but I may need an audio-only or low-bandwidth option
   - No

8. **Are you willing to complete all three parts?**

   Checkbox confirmation. Required.
   - Product test of up to 45 minutes
   - Interview of up to 20 minutes
   - Short follow-up within seven days

9. **Are you comfortable using experimental software on CKB Pudge testnet?**

   Single choice. Required.
   - Yes
   - I would like more information first
   - No

10. **Please confirm the incentive status.**

    Checkbox. Required.
    - I understand that the proposed $30 incentive depends on grant approval and
      is not currently guaranteed.

## Receiver Owner Or Operator Branch

Show this section when the applicant selects `Receiver owner or operator`.

11. **Do you operate an ADS-B or Mode S receiver now, or have you operated one
    during the last 12 months?**

    Single choice. Required.
    - I operate one now
    - I operated one within the last 12 months
    - Neither

12. **When was the receiver last active?**

    Month and year. Required. Do not request its location.

13. **What receiver hardware and software do you use or maintain?**

    Long answer. Required. Do not request serial numbers, credentials, or network
    addresses.

14. **How many receivers do you operate or help maintain?**

    Single choice. Required.
    - 1
    - 2-3
    - 4-10
    - More than 10

15. **Briefly describe the most recent time you added, replaced, moved,
    transferred, or retired a receiver. How did you update its identity, owner,
    or status?**

    Long answer. Required. Add: "Do not share credentials or a precise
    location."

16. **Can you install or use a supported CKB Pudge testnet wallet for the study?**

    Single choice. Required.
    - Yes
    - Probably, with setup instructions
    - No

## Coordinator Or Developer Branch

Show this section when the applicant selects `Receiver-network coordinator` or
`Developer or maintainer of receiver-network software`.

11. **How many receivers are involved in the system or project you help
    maintain?**

    Single choice. Required.
    - 2-3
    - 4-10
    - 11-50
    - More than 50

12. **What work have you done with receiver inventory, feeder management, MLAT,
    monitoring, APIs, data export, or network software?**

    Long answer. Required.

13. **Briefly describe the most recent receiver inventory or integration change
    you made. What systems or people were involved?**

    Long answer. Required. Do not request internal credentials or private
    endpoints.

14. **Which follow-up could you realistically complete within seven days?**

    Multiple choice. Required.
    - Test a small JSON import
    - Review the public API/schema and estimate integration work
    - Record an integration decision, next step, and blockers
    - None of these

## Verification And Contact

17. **How may we verify your relevant experience?**

    Multiple choice. Required.
    - Public feeder, profile, or project link
    - Redacted receiver-software status screenshot
    - Redacted photograph of a receiver setup
    - Private project evidence shared directly with the researcher

18. **Link or short description of the evidence**

    Long answer. Required. Add: "Evidence will not be published without separate
    permission. Do not include credentials, IP addresses, or an exact receiver
    location."

19. **Why are you interested in this pilot, and what would make the session
    useful to you?**

    Long answer. Optional. Do not use this answer to replace role eligibility.

20. **May the researcher contact you about this pilot using the contact method
    you provided?**

    Single choice. Required.
    - Yes
    - No

21. **Final acknowledgement**

    Checkbox. Required.
    - I understand that applying does not guarantee selection, participation is
      voluntary, and I may decline or stop at any time.

## Submission Confirmation

Thank you. Your application has been received. It is an expression of interest,
not a confirmed pilot place. The researcher will contact selected applicants
after checking role fit, cohort balance, availability, and technical readiness.
Do not send wallet secrets, receiver credentials, or precise receiver locations
by email or message.

Questions or withdrawal requests: `[PROJECT EMAIL]`

Privacy contact and response retention period: `[PRIVACY CONTACT AND RETENTION
PERIOD]`

## Before Publishing The Form

- Replace every bracketed placeholder.
- Add the application's closing date and scheduling time zone.
- State where private responses are stored, who can access them, and when they
  will be deleted.
- Enable branching so applicants see only their role-specific questions.
- Disable public response summaries and automatic collection of unrelated
  account information.
- Do not enable file uploads unless the storage location and deletion policy are
  acceptable. A private follow-up is safer for verification evidence.
- Test the form once as an operator and once as a coordinator.
- Do not schedule sessions until [READINESS_GATE.md](READINESS_GATE.md) passes.
