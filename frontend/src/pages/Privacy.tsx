import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Seo from "@/components/Seo";
import TextScrim from "@/components/TextScrim";
import { useFadeUp } from "@/hooks/useReveal";

const LAST_UPDATED = "July 9, 2026";

export default function Privacy() {
  const fadeUp = useFadeUp();

  return (
    <>
      <Seo
        title="Privacy Policy | Ashford & Briggs"
        description="How Ashford & Briggs LLC collects, uses, and protects information across ashfordbriggs.com and the Paladin service."
        path="/privacy"
      />
      <article className="container" style={{ maxWidth: 780, padding: "100px 24px 90px" }}>
        <TextScrim>
          <motion.div {...fadeUp}>
            <span className="eyebrow">Legal</span>
            <h1 style={{ fontSize: "clamp(30px, 5vw, 46px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.15, margin: "16px 0 12px" }}>
              Privacy Policy
            </h1>
            <p style={{ color: "var(--text-dim)", fontSize: 14, fontFamily: "var(--font-mono)", marginBottom: 8 }}>
              Last updated: {LAST_UPDATED}
            </p>

            <div className="prose" style={{ marginTop: 36 }}>
              <p>
                Ashford &amp; Briggs LLC ("<strong>Ashford &amp; Briggs</strong>," "<strong>we</strong>,"
                "<strong>us</strong>," or "<strong>our</strong>") builds Paladin, real-time AI
                intelligence for recruiter phone calls ("<strong>Paladin</strong>" or the
                "<strong>Service</strong>"). This Privacy Policy explains how we collect, use,
                disclose, and safeguard information when you visit ashfordbriggs.com (the
                "<strong>Site</strong>"), request a demo, or use the Service as an authorized
                customer, administrator, or user ("<strong>you</strong>").
              </p>
              <p>
                This Policy is written to be accurate to how our systems actually work today,
                and it will change as the Service evolves. If you have questions after reading
                it, contact us — see <a href="#contact">Section&nbsp;15</a>.
              </p>

              <h2 id="information-we-collect">1. Information We Collect</h2>
              <p>We collect information in three general ways: what you give us directly, what
                our systems generate automatically, and — for active customers — the call and
                candidate data Paladin processes to deliver the Service.</p>

              <h3>1.1 Information you provide directly</h3>
              <ul>
                <li><strong>Demo and sales inquiries.</strong> When you request a demo or contact
                  us through the Site, we collect your name, company, work email, phone number
                  (optional), role, team size, and any message you include.</li>
                <li><strong>Account information.</strong> If you're issued an administrator or
                  user account (for example, to manage a Paladin subscription or author content
                  on our behalf), we collect your name, email address, and a securely hashed
                  password. We never store your password in plain text.</li>
                <li><strong>Correspondence.</strong> If you email us or reply to a message from
                  us, we keep that correspondence, including the content of your message and our
                  response, to respond to you and maintain a record of the interaction.</li>
              </ul>

              <h3>1.2 Information collected automatically</h3>
              <p>
                Our web server logs standard technical data for every request — IP address,
                browser and device type, pages visited, referring page, and timestamps — which
                we use for security, abuse prevention, and diagnosing problems with the Site.
              </p>
              <p>
                As of the date above, <strong>ashfordbriggs.com does not use third-party
                advertising or analytics cookies</strong>, and does not sell or share your
                browsing activity with data brokers or ad networks. See <a href="#cookies">Section&nbsp;12</a> for
                the specifics on cookies and local storage.
              </p>

              <h3>1.3 Call, transcript, and candidate data (Paladin customers)</h3>
              <p>
                Paladin's core function is to listen to a live recruiting call and provide the
                recruiter with real-time intelligence. If your organization is a Paladin
                customer, using the Service involves the following categories of data:
              </p>
              <ul>
                <li><strong>Candidate materials.</strong> LinkedIn profile URLs, résumés, and job
                  descriptions that a recruiter supplies before a call, used to generate a
                  pre-call skills-gap analysis.</li>
                <li><strong>Live call audio and transcription.</strong> While a call is in
                  progress, Paladin processes the audio of both participants to produce a live
                  transcript, contextual prompts, and on-screen definitions.</li>
                <li><strong>Post-call outputs.</strong> Summaries, skills-match and culture-fit
                  confidence scores, and any notes generated after the call ends.</li>
                <li><strong>Call metadata.</strong> Call duration, timestamps, and the phone
                  numbers or extensions involved in connecting the call.</li>
              </ul>
              <p>
                This data is generated and used <em>by our customers, for their own recruiting
                purposes</em>. For candidate and call data, Ashford &amp; Briggs acts as a data
                processor (or "service provider," as that term is used under the CCPA/CPRA) on
                behalf of the Paladin customer, who is the data controller (or "business")
                responsible for that data — our processing is governed by that customer's
                instructions and our agreement with them. If you are a job candidate and have
                questions about a specific call, the recruiter or company you spoke with is your
                primary point of contact, since they control that data; you're welcome to also
                contact us and we will direct your request appropriately.
              </p>
              <p>
                Ashford &amp; Briggs personnel do not routinely access the content of a customer's
                call recordings, transcripts, or candidate materials. Limited, logged access may
                occur where necessary to provide customer support, investigate a reported issue,
                or maintain the security and reliability of the Service.
              </p>

              <h3>1.4 Voice and biometric information</h3>
              <p>
                Live call audio may constitute biometric information under some state laws (for
                example, Illinois, Texas, and Washington). Paladin is designed to transcribe and
                analyze call content — it is not designed to identify or authenticate individuals
                by their voice. Where applicable law requires a written retention and destruction
                schedule for biometric identifiers, we maintain one and will provide it on
                request, and we do not retain call audio longer than described in{" "}
                <a href="#data-retention">Section&nbsp;7</a>.
              </p>

              <h2 id="how-we-use-information">2. How We Use Information</h2>
              <p>We use the information described above to:</p>
              <ul>
                <li>Provide, operate, and maintain the Site and the Service;</li>
                <li>Respond to demo requests, support questions, and other inquiries;</li>
                <li>Generate the pre-call analysis, live prompts, and post-call summaries that
                  are the point of Paladin;</li>
                <li>Authenticate administrators and enforce role-based access to our admin
                  tools;</li>
                <li>Detect, investigate, and prevent fraud, abuse, and security incidents;</li>
                <li>Comply with legal obligations and enforce our
                  {" "}<Link to="/terms">Terms of Service</Link>; and</li>
                <li>Improve the Site and the Service, including by understanding aggregate usage
                  patterns.</li>
              </ul>
              <p>
                We do not use candidate call data to build generalized AI models that are shared
                across customers, and we do not sell personal information, as those terms are
                defined under applicable law.
              </p>

              <h2 id="legal-bases">3. Legal Bases for Processing</h2>
              <p>
                Where applicable data protection law (such as the EU or UK GDPR) requires a legal
                basis for processing, we rely on: performance of a contract (to provide the
                Service you or your employer has signed up for), our legitimate interests (to
                secure, support, and improve the Service), your consent (where we ask for it
                specifically, such as certain marketing communications), and compliance with
                legal obligations.
              </p>

              <h2 id="how-we-share-information">4. How We Share Information</h2>
              <p>
                We do not sell your personal information. We share it only in the following
                circumstances:
              </p>
              <h3>4.1 Service providers (subprocessors)</h3>
              <p>We use a small number of carefully selected vendors to operate the Service:</p>
              <ul>
                <li><strong>Cloud hosting and database.</strong> Our application and database
                  infrastructure runs on third-party cloud hosting providers, who store data on
                  our behalf under contractual confidentiality and security obligations.</li>
                <li><strong>AI processing.</strong> We use Anthropic's Claude models, via a
                  server-side proxy that never exposes our API credentials to your browser, to
                  power AI-assisted features — including marketing blog drafting on this Site and
                  the analysis, prompts, and summaries at the heart of the Paladin Service.
                  Anthropic processes this data as our subprocessor and does not use it to train
                  its own models.</li>
                <li><strong>Outbound email.</strong> When a customer replies to a demo request or
                  other inquiry, that email is sent through an SMTP server that the customer
                  configures and controls themselves (for example, their own corporate mail
                  provider) — we do not route customer email traffic through a shared third-party
                  marketing-email platform. Connection credentials for that SMTP server are
                  encrypted at rest.</li>
              </ul>
              <h3>4.2 Legal and safety</h3>
              <p>
                We may disclose information if required by law, subpoena, or other legal
                process, or where we believe in good faith that disclosure is necessary to
                protect the rights, property, or safety of Ashford &amp; Briggs, our users, or
                the public.
              </p>
              <h3>4.3 Business transfers</h3>
              <p>
                If Ashford &amp; Briggs is involved in a merger, acquisition, financing, or sale
                of assets, information may be transferred as part of that transaction. We will
                notify you of any such change in ownership or use of your personal information.
              </p>

              <h2 id="call-recording">5. Call Recording, Monitoring &amp; Consent</h2>
              <p>
                Because Paladin listens to and analyzes live phone calls, call recording and
                wiretapping laws apply. These laws vary significantly by state and country — some
                jurisdictions (including Florida, where we're headquartered) require the consent
                of <em>every</em> party to a call before it can be recorded or monitored, while
                others require only one party's consent.
              </p>
              <p>
                <strong>Obtaining and documenting the legally required consent from call
                participants is the responsibility of the Paladin customer initiating the call</strong>,
                not Ashford &amp; Briggs. Our
                {" "}<Link to="/terms">Terms of Service</Link> require every customer to comply
                with all call-recording and consent laws applicable to their calls. If you are a
                candidate and believe a call involving you was recorded or monitored without
                appropriate consent, please contact the recruiter or employer directly, and feel
                free to also reach out to us.
              </p>

              <h2 id="ai-generated-outputs">6. AI-Generated Outputs</h2>
              <p>
                Skills-gap scores, culture-fit indicators, live prompts, and summaries generated
                by Paladin are produced by AI models and are intended as a decision-support tool
                for a human recruiter — not an automated basis for hiring decisions. We encourage
                customers to review our Terms of Service for the disclaimers that apply to
                AI-generated content, and to use professional judgment alongside, not in place
                of, these outputs.
              </p>

              <h2 id="data-retention">7. Data Retention</h2>
              <p>
                We retain personal information for as long as necessary to provide the Site and
                the Service, comply with our legal obligations, resolve disputes, and enforce our
                agreements. Call recordings, transcripts, and related outputs are retained for no
                more than ninety (90) days after the end of a customer's subscription, unless a
                shorter or longer period is specified in that customer's service agreement or
                account settings. Demo request and inquiry records are retained as long as
                reasonably useful for following up, and are periodically reviewed for deletion. If
                you're a candidate and would like your call data deleted, you may contact us
                directly and we will honor that request consistent with our role as processor and
                our contractual obligations to the relevant customer.
              </p>

              <h2 id="data-security">8. Data Security</h2>
              <p>
                We use industry-standard safeguards to protect information, including encrypted
                connections (TLS) for data in transit, bcrypt password hashing, role-based access
                controls on administrative functions, encryption at rest for sensitive
                credentials such as stored email server passwords, and rate limiting on
                public-facing endpoints to reduce abuse. No method of transmission or storage is
                completely secure, and we cannot guarantee absolute security, but we work to
                protect your information and to improve these safeguards over time. If we become
                aware of a security incident that compromises your personal information in a
                manner that triggers a legal notification obligation, we will notify affected
                individuals and/or the relevant Paladin customer without unreasonable delay and in
                accordance with applicable law, including the Florida Information Protection Act.
              </p>

              <h2 id="your-privacy-rights">9. Your Privacy Rights</h2>
              <p>
                Depending on where you live, you may have rights to access, correct, delete, or
                receive a copy of your personal information, and to opt out of certain uses.
              </p>
              <h3>9.1 California and other U.S. state privacy rights</h3>
              <p>
                In the preceding twelve months, we have collected the following categories of
                personal information, as defined by the CCPA: identifiers (name, email, phone);
                professional or employment-related information (résumés, job descriptions,
                role/title); audio and electronic information (call recordings and transcripts);
                internet or network activity (device and browser data from Site visits); and
                inferences (skills-match and culture-fit indicators). We have disclosed
                identifiers, professional/employment information, and audio/electronic information
                to the service providers described in{" "}
                <a href="#how-we-share-information">Section&nbsp;4</a> for the business purposes
                described in <a href="#how-we-use-information">Section&nbsp;2</a>. We have not
                sold or shared any of these categories.
              </p>
              <p>
                Some candidate materials and call content may include sensitive personal
                information under the CPRA (for example, information that could reveal health,
                immigration, or similar status). We use this information only to provide the
                Service as instructed by the relevant customer, and not to infer characteristics
                about you for other purposes.
              </p>
              <p>
                Residents of California and other states with comprehensive privacy laws may have
                the right to know what personal information we hold about you, request deletion
                or correction, opt out of the "sale" or "sharing" of personal information (as
                those terms are defined by applicable law — we do not sell or share personal
                information for cross-context behavioral advertising), and limit the use of
                sensitive personal information. To exercise these rights, contact us using the
                details in <a href="#contact">Section&nbsp;15</a>. We will not discriminate
                against you for exercising these rights.
              </p>
              <h3>9.2 EU/UK/EEA visitors</h3>
              <p>
                If you're located in the European Economic Area or the United Kingdom, you may
                have rights under the GDPR or UK GDPR to access, rectify, erase, restrict, or
                port your personal data, and to object to certain processing. You also have the
                right to lodge a complaint with your local data protection authority. Contact us
                to exercise these rights. We are a U.S. company; if we later determine that we are
                required to appoint an EU or UK representative under Article&nbsp;27 of the
                GDPR/UK&nbsp;GDPR, we will identify that representative's contact details here.
              </p>
              <h3>9.3 Verifying and responding to requests</h3>
              <p>
                We may need to verify your identity before completing a request, and we will
                respond within the time required by applicable law. If you're a job candidate
                asking about call data, we may direct you to the specific customer who controls
                that data, since they are best positioned to fulfill certain requests.
              </p>

              <h2 id="childrens-privacy">10. Children's Privacy</h2>
              <p>
                The Site and the Service are directed at businesses and working professionals and
                are not intended for individuals under 18. We do not knowingly collect personal
                information from children. If you believe a child has provided us with personal
                information, please contact us and we will take appropriate steps to delete it.
              </p>

              <h2 id="international-transfers">11. International Data Transfers</h2>
              <p>
                We are based in the United States, and information we collect may be stored and
                processed in the United States or other countries where our service providers
                operate. Where required, we use appropriate safeguards for international transfers
                of personal data — standard contractual clauses approved by the European
                Commission for transfers from the EEA and Switzerland, and the UK International
                Data Transfer Agreement (or the UK Addendum to the EU standard contractual
                clauses) for transfers from the United Kingdom.
              </p>

              <h2 id="cookies">12. Cookies &amp; Local Storage</h2>
              <p>
                The public marketing site does not set tracking or advertising cookies. Our admin
                application uses your browser's local storage (not a cookie) to hold a session
                token after you sign in, purely so you stay logged in between page loads — this
                mechanism is not used for cross-site tracking and is cleared when you sign out.
                If that changes — for example, if we add product analytics — we will update this
                Policy first.
              </p>

              <h2 id="third-party-links">13. Third-Party Links</h2>
              <p>
                The Site may link to third-party websites, such as LinkedIn. We aren't responsible
                for the privacy practices of sites we don't operate, and we encourage you to
                review their policies before providing information to them.
              </p>

              <h2 id="changes-to-policy">14. Changes to This Policy</h2>
              <p>
                We may update this Privacy Policy from time to time. If we make material changes,
                we'll update the "Last updated" date above and, where appropriate, provide
                additional notice (such as a notice on the Site or an email to account
                administrators). Your continued use of the Site or the Service after an update
                constitutes acceptance of the revised Policy.
              </p>

              <h2 id="contact">15. Contact Us</h2>
              <p>
                If you have questions about this Privacy Policy or how we handle your
                information, contact us at{" "}
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
