import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Seo from "@/components/Seo";
import TextScrim from "@/components/TextScrim";
import { useFadeUp } from "@/hooks/useReveal";

const LAST_UPDATED = "July 9, 2026";

export default function Terms() {
  const fadeUp = useFadeUp();

  return (
    <>
      <Seo
        title="Terms of Service | Ashford & Briggs"
        description="The terms governing your access to and use of ashfordbriggs.com and the Paladin service, provided by Ashford & Briggs LLC."
        path="/terms"
      />
      <article className="container" style={{ maxWidth: 780, padding: "100px 24px 90px" }}>
        <TextScrim>
          <motion.div {...fadeUp}>
            <span className="eyebrow">Legal</span>
            <h1 style={{ fontSize: "clamp(30px, 5vw, 46px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.15, margin: "16px 0 12px" }}>
              Terms of Service
            </h1>
            <p style={{ color: "var(--text-dim)", fontSize: 14, fontFamily: "var(--font-mono)", marginBottom: 8 }}>
              Last updated: {LAST_UPDATED}
            </p>

            <div className="prose" style={{ marginTop: 36 }}>
              <p>
                These Terms of Service ("<strong>Terms</strong>") are a binding agreement between
                you (and, if applicable, the organization you represent, "<strong>you</strong>" or
                "<strong>Customer</strong>") and Ashford &amp; Briggs LLC ("<strong>Ashford &amp;
                Briggs</strong>," "<strong>we</strong>," "<strong>us</strong>," or "<strong>our</strong>"),
                governing your access to and use of ashfordbriggs.com (the "<strong>Site</strong>")
                and Paladin, our real-time AI intelligence service for recruiter phone calls (the
                "<strong>Service</strong>"). By accessing the Site, requesting a demo, or using
                the Service, you agree to these Terms. If you don't agree, don't use the Site or
                the Service.
              </p>
              <p>
                Please also review our{" "}
                <Link to="/privacy">Privacy Policy</Link>, which describes how we handle
                information and is incorporated into these Terms by reference.
              </p>

              <h2 id="description-of-service">1. Description of the Service</h2>
              <p>
                Paladin provides real-time intelligence during live recruiting phone calls,
                delivered through the recruiter's existing phone — Paladin calls the recruiter
                first, then dials and bridges the candidate. The Service may include, depending on
                your plan: pre-call skills-gap analysis generated from candidate materials you
                supply (such as a LinkedIn URL, résumé, or job description); live, on-screen
                prompts and jargon definitions during the call; and a post-call summary with
                skills-match and culture-fit indicators. We may add, change, or remove features at
                any time.
              </p>

              <h2 id="eligibility-accounts">2. Eligibility &amp; Accounts</h2>
              <p>
                You must be at least 18 years old and able to form a binding contract to use the
                Service. If you create or are issued an account, you're responsible for
                maintaining the confidentiality of your login credentials and for all activity
                under your account. Notify us promptly of any unauthorized use. We may suspend or
                terminate accounts that provide false information or violate these Terms.
              </p>

              <h2 id="subscriptions-fees">3. Subscriptions &amp; Fees</h2>
              <p>
                Access to the Service is provided under a subscription or order agreed between
                Ashford &amp; Briggs and Customer, which will specify applicable fees, billing
                frequency, and term. Unless the order says otherwise, subscriptions renew
                automatically at the end of each term at then-current rates, and fees are
                non-refundable except as required by law or as we expressly agree in writing. You
                are responsible for any taxes associated with your purchase, other than taxes on
                our net income.
              </p>
              <p>
                If any invoiced amount is not received by its due date, we may suspend your access
                to the Service, after written notice, until payment is received, without relieving
                you of the obligation to pay fees accrued during the suspension. This right is
                independent of, and does not require, a determination that you have otherwise
                breached these Terms.
              </p>

              <h2 id="call-recording-consent">4. Call Recording, Monitoring &amp; Your Legal Responsibility</h2>
              <p>
                <strong>This section is important — please read it carefully.</strong> The Service
                listens to, transcribes, and analyzes live telephone conversations. Recording or
                monitoring a phone call without the legally required consent of the people on the
                call is illegal in many jurisdictions. Consent requirements vary by state and
                country: some jurisdictions permit recording with the consent of just one party to
                the call (which may be you), while a significant number of jurisdictions —
                including Florida, where we're headquartered — require the consent of{" "}
                <em>every</em> party on the call. In addition to state law, the federal Wiretap Act
                (18&nbsp;U.S.C. §2510 et seq.) prohibits intercepting, disclosing, or using the
                contents of a call without required consent, and provides for civil damages and
                criminal penalties. This summary is provided for general informational purposes
                only, does not constitute legal advice, and is not a substitute for consultation
                with your own counsel regarding the laws applicable to your calls.
              </p>
              <p>You represent, warrant, and agree that:</p>
              <ul>
                <li>You are solely responsible for determining which call-recording, wiretapping,
                  and consent laws apply to each call you make using the Service, based on your
                  location, the candidate's location, and any other applicable jurisdiction;</li>
                <li>You will obtain any consent required by applicable law from every participant
                  on a call before using the Service to monitor or record that call, and you will
                  do so in a manner that satisfies the applicable legal standard (which may
                  require an affirmative, verbal acknowledgment at the start of the call, not
                  merely a written policy);</li>
                <li>You will not use the Service in connection with any call where you do not have
                  the legal right to record or monitor the conversation; and</li>
                <li>You will comply with all other applicable laws relating to your use of the
                  Service, including employment and anti-discrimination law.</li>
              </ul>
              <p>
                Ashford &amp; Briggs provides the Service solely as your technology and
                communications processor, acting at your direction and under your instruction to
                place, connect, and process each call you initiate through Paladin. We do not
                independently decide to record or monitor any call, select who is called, or use
                call content for any purpose other than delivering the Service to you, and we are
                not a participant in the substance of your conversations. We do not determine, on
                your behalf, whether consent is required or has been obtained, and we reserve the
                right to suspend or refuse to process any call where we have a good-faith reason to
                believe required consent was not obtained. We may, at our discretion, provide
                features intended to help facilitate consent (such as an audible notice at the
                start of a call). Any such feature is provided as a convenience only and does not,
                by itself, satisfy the consent standard required in your jurisdiction — some
                jurisdictions require an affirmative verbal acknowledgment from each participant,
                not merely an audible tone. If enabled, this notice occurs before candidate audio
                is captured or analyzed, but you remain solely responsible for confirming it
                satisfies applicable law. The ultimate legal responsibility for compliance rests
                with you, and you agree to indemnify us for claims arising from your failure to
                comply with this Section, as described in{" "}
                <a href="#indemnification">Section&nbsp;12</a>.
              </p>

              <h2 id="candidate-data">5. Candidate Data &amp; Third-Party Information</h2>
              <p>
                You represent that you have the right to submit any candidate information —
                including résumés, LinkedIn profile data, job descriptions, and call audio — to
                the Service, and that doing so, and our processing of it as described in the{" "}
                <Link to="/privacy">Privacy Policy</Link>, does not violate any third party's
                rights or any applicable law, including candidate privacy and data protection
                laws. You are responsible for providing any notices to, and obtaining any consents
                from, candidates that applicable law requires in connection with your use of the
                Service.
              </p>

              <h2 id="acceptable-use">6. Acceptable Use</h2>
              <p>You agree not to:</p>
              <ul>
                <li>Use the Service for any illegal purpose, or in a way that violates any
                  applicable law or regulation, including anti-discrimination and fair-hiring
                  laws;</li>
                <li>Use the Service to harass, defame, or invade the privacy of any person;</li>
                <li>Attempt to reverse-engineer, decompile, or access the source code of the
                  Service, except to the extent applicable law prohibits this restriction;</li>
                <li>Probe, scan, or attempt to circumvent any security or authentication measure
                  of the Site or the Service;</li>
                <li>Use the Service to build a competing product, or resell or sublicense access
                  to the Service without our written consent;</li>
                <li>Upload or transmit any virus, malware, or other harmful code; or</li>
                <li>Use the Service if you are located in, or a national or resident of, any
                  country or region subject to U.S. government embargo or sanctions, or if you are
                  listed on any U.S. government list of prohibited or restricted parties.</li>
              </ul>
              <p>
                You represent that you are not subject to the sanctions and export-control
                restriction above, and you agree that you will not use the Service in violation of
                applicable export control or sanctions laws.
              </p>

              <h2 id="ai-generated-content">7. AI-Generated Content &amp; Hiring Decisions</h2>
              <p>
                Skills-gap analyses, live prompts, jargon definitions, culture-fit indicators, and
                post-call summaries produced by the Service are generated using artificial
                intelligence and are provided as a <strong>decision-support tool for a human
                recruiter</strong> — they are not verified facts, and they are not, on their own,
                a lawful or reliable basis for any hiring decision. AI-generated outputs may be
                incomplete, inaccurate, or reflect biases present in underlying models or
                training data. You agree that you will not rely solely on AI-generated outputs
                from the Service to make hiring, compensation, promotion, or other employment
                decisions, and that a qualified human remains responsible for those decisions and
                for compliance with applicable employment and anti-discrimination law. Ashford
                &amp; Briggs disclaims responsibility for employment decisions made using the
                Service.
              </p>
              <p>
                Some jurisdictions impose specific legal requirements on employers and staffing
                agencies that use automated or AI-assisted tools in hiring — for example,
                bias-audit and candidate-notice requirements under laws such as New York City Local
                Law 144, the Illinois AI Video Interview Act, and evolving state and international
                AI-employment regulations (including the EU AI Act's treatment of
                recruitment-related AI as high-risk). You are responsible for determining whether
                such laws apply to your use of the Service and for satisfying any applicable
                notice, audit, or disclosure obligations independent of this Section.
              </p>

              <h2 id="intellectual-property">8. Intellectual Property</h2>
              <p>
                Ashford &amp; Briggs owns all right, title, and interest in and to the Site, the
                Service, and all related technology, software, and content we provide, excluding
                any content or data you submit ("<strong>Customer Data</strong>"). Subject to
                these Terms, we grant you a limited, non-exclusive, non-transferable license to
                access and use the Service for your internal business purposes during your
                subscription term. You retain all rights to your Customer Data, and you grant us a
                license to use it solely to provide, maintain, and improve the Service for you, as
                described in our <Link to="/privacy">Privacy Policy</Link>. If you provide feedback
                or suggestions about the Service, you grant us a perpetual, royalty-free license to
                use them for any purpose, with no obligation to compensate or credit you.
              </p>

              <h2 id="confidentiality">9. Confidentiality</h2>
              <p>
                Each party may have access to the other's non-public business, technical, or
                product information ("<strong>Confidential Information</strong>"). Each party
                agrees to protect the other's Confidential Information with the same degree of
                care it uses for its own similar information (and no less than reasonable care),
                and to use it only to perform its obligations or exercise its rights under these
                Terms. This section does not apply to information that is or becomes public
                through no fault of the receiving party, was already known to the receiving
                party, or is independently developed.
              </p>

              <h2 id="disclaimers">10. Disclaimers</h2>
              <p>
                THE SITE AND THE SERVICE ARE PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT
                WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING IMPLIED
                WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND
                NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED,
                ERROR-FREE, OR COMPLETELY SECURE, OR THAT ANY AI-GENERATED OUTPUT WILL BE ACCURATE
                OR COMPLETE. SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF CERTAIN WARRANTIES,
                SO SOME OF THE ABOVE EXCLUSIONS MAY NOT APPLY TO YOU. We do not currently offer a
                service-level agreement or uptime commitment as part of standard subscriptions;
                specific availability commitments, if any, will be set out in a separate written
                order or SLA addendum.
              </p>

              <h2 id="limitation-of-liability">11. Limitation of Liability</h2>
              <p>
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, ASHFORD &amp; BRIGGS AND ITS OFFICERS,
                EMPLOYEES, AND AGENTS WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
                CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, REVENUE, DATA, OR
                GOODWILL, ARISING FROM OR RELATED TO YOUR USE OF THE SITE OR THE SERVICE, EVEN IF
                WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. OUR TOTAL LIABILITY FOR
                ANY CLAIM ARISING OUT OF OR RELATING TO THESE TERMS OR THE SERVICE WILL NOT EXCEED
                THE AMOUNT YOU PAID US FOR THE SERVICE IN THE TWELVE (12) MONTHS BEFORE THE CLAIM
                AROSE. SOME JURISDICTIONS DO NOT ALLOW THE LIMITATION OR EXCLUSION OF CERTAIN
                DAMAGES, SO SOME OF THE ABOVE LIMITATIONS MAY NOT APPLY TO YOU.
              </p>

              <h2 id="indemnification">12. Indemnification</h2>
              <p>
                You agree to defend, indemnify, and hold harmless Ashford &amp; Briggs and its
                officers, employees, and agents from and against any claims, damages, losses, and
                expenses (including reasonable attorneys' fees) arising out of or related to: (a)
                your breach of these Terms, including{" "}
                <a href="#call-recording-consent">Section&nbsp;4</a> (Call Recording, Monitoring
                &amp; Your Legal Responsibility); (b) your violation of any applicable law; (c)
                your Customer Data or its use with the Service; or (d) any employment, hiring,
                compensation, or promotion decision you make using or informed by the Service,
                including reliance on AI-generated outputs described in{" "}
                <a href="#ai-generated-content">Section&nbsp;7</a>.
              </p>

              <h2 id="term-termination">13. Term &amp; Termination</h2>
              <p>
                These Terms remain in effect for as long as you use the Site or the Service. We
                may suspend or terminate your access if you materially breach these Terms and
                don't cure the breach within a reasonable period after notice, or immediately if
                necessary to protect the Service, other users, or comply with law. You may stop
                using the Service at any time; subscription cancellation is governed by your order
                agreement. Upon termination or expiration of your subscription, you may request an
                export of your Customer Data for thirty (30) days following the effective date of
                termination. After that period, we may delete or de-identify Customer Data from our
                production systems in accordance with the retention practices described in our{" "}
                <Link to="/privacy">Privacy Policy</Link>, and we have no obligation to retain it
                further. Sections that by their nature should survive termination — including
                Intellectual Property, Confidentiality, Disclaimers, Limitation of Liability,
                Indemnification, and Governing Law — will survive.
              </p>

              <h2 id="governing-law">14. Governing Law &amp; Dispute Resolution</h2>
              <p>
                These Terms are governed by the laws of the State of Florida, without regard to
                its conflict-of-laws principles. Subject to any mandatory consumer-protection law
                to the contrary, you and Ashford &amp; Briggs agree that any dispute arising out
                of or relating to these Terms or the Service will be brought exclusively in the
                state or federal courts located in Duval County, Florida, and you consent to
                personal jurisdiction there.
              </p>

              <h2 id="changes-to-terms">15. Changes to These Terms</h2>
              <p>
                We may update these Terms from time to time. If we make material changes, we'll
                update the "Last updated" date above and, where appropriate, provide additional
                notice. Continued use of the Site or the Service after an update constitutes
                acceptance of the revised Terms.
              </p>

              <h2 id="miscellaneous">16. Miscellaneous</h2>
              <p>
                These Terms, together with any order agreement and our{" "}
                <Link to="/privacy">Privacy Policy</Link>, constitute the entire agreement between
                you and Ashford &amp; Briggs regarding the Site and the Service. If any provision
                of these Terms is found unenforceable, the remaining provisions remain in full
                effect. Our failure to enforce any right or provision is not a waiver of that
                right or provision. You may not assign these Terms without our prior written
                consent; we may assign these Terms in connection with a merger, acquisition, or
                sale of assets. Neither party is liable for delays caused by circumstances beyond
                its reasonable control. Nothing in these Terms creates a partnership, joint
                venture, agency, or employment relationship between the parties; each party is an
                independent contractor. These Terms do not create any third-party beneficiary
                rights, including for any candidate whose information is processed through the
                Service.
              </p>
              <p>
                Any notice under these Terms must be in writing and is deemed given: (a) to you,
                when sent to the email address associated with your account or order; and (b) to
                us, when sent to{" "}
                <a href="mailto:inquiries@ashfordbriggs.com">inquiries@ashfordbriggs.com</a>.
                Notices are deemed received on the date sent.
              </p>

              <h2 id="contact">17. Contact Us</h2>
              <p>
                Questions about these Terms? Contact us at{" "}
                <a href="mailto:inquiries@ashfordbriggs.com">inquiries@ashfordbriggs.com</a>, or:
              </p>
              <p>
                Ashford &amp; Briggs LLC<br />
                Jacksonville, Florida, United States
              </p>
            </div>
          </motion.div>
        </TextScrim>
      </article>
    </>
  );
}
