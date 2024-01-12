```markdown
# Email Security Checker

This Python script connects to your email inbox, waits for new emails, and performs checks to identify potentially suspicious emails based on common security policies.

## Getting Started

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/yourusername/email-security-checker.git
   ```

2. Install the required dependencies:

   ```bash
   pip install imaplib
   ```

3. Run the script:

   ```bash
   python email_security_checker.py
   ```

4. Follow the on-screen prompts to enter your email credentials and IMAP server address.

## Known Phishing Domains

The list of known phishing domains used in this application was sourced from the Cloudflare blog's list of the "50 Most Impersonated Brands to Protect Against Phishing". You can find the original list [here](https://blog.cloudflare.com/50-most-impersonated-brands-protect-phishing).

Feel free to update the `known_phishing_domains` list in the script with additional domains based on your organization's policies or other reliable sources.

## Trusted Domains

The `trusted_domains` list in the script contains examples of trusted domains. Replace these with the actual domains you consider trustworthy.

## Security Checks

The script performs several security checks on each email, including looking for specific keywords in the subject, checking for known phishing domains, and verifying the sender's domain against trusted domains. Additional checks can be added or modified based on your organization's security policies.

## Disclaimer

This script is a basic example and may need adjustments based on your specific requirements and email provider settings. Use it responsibly and adapt it to suit your organization's security policies.

## License

This project is licensed under the [MIT License](LICENSE).
```