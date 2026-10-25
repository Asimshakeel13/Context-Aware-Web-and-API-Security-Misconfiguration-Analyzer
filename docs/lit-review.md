# Literature review

## CVSS v3.1 environmental metrics

- What are the environmental metrics and how do CR, IR, and AR alter base risk?
- How should modified base metrics and security requirements be applied?
- Which implementation and rounding details must CAWASMA preserve?

## OWASP Top 10 2021 and ASVS

- Which OWASP Top 10 2021 categories map to CAWASMA checks?
- Which ASVS requirements provide testable controls for black-box scanning?
- Where do OWASP and ASVS leave gaps for context-aware prioritisation?

## Context-aware vulnerability scoring

- Which papers score vulnerabilities using endpoint, asset, or data context?
- What contextual features, labels, and evaluation methods do they use?
- How does CAWASMA differ in sensitivity and response-body prioritisation?

## Existing scanner scoring

### Burp Suite

- How does Burp rank or report findings?
- What context does it use, and what does it omit?

### OWASP ZAP

- How are ZAP risk and confidence levels assigned?
- What are the limits of static risk tiers for endpoint context?

### Nikto

- How does Nikto report severity or prioritisation?
- What constraints follow from its signature-based approach?

### Nuclei

- How do template severity and tags influence Nuclei output?
- What contextual scoring and response analysis are unavailable?

## Synthesis

- What research gap does CAWASMA address?
- Which claims require experimental evidence in the evaluation?
