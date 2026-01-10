"""Configuration for SaaS Opportunity Bot"""

# High-value industries (customers with resources)
INDUSTRIES = {
    "finance": ["fintech", "banking", "trading", "investment", "accounting", "bookkeeping", "tax", "CFO", "financial"],
    "legal": ["lawyer", "attorney", "law firm", "legal tech", "contract", "compliance", "paralegal"],
    "healthcare": ["medical", "healthcare", "clinic", "hospital", "doctor", "patient", "HIPAA", "telehealth"],
    "real_estate": ["real estate", "realtor", "property", "landlord", "rental", "mortgage", "broker"],
    "saas_b2b": ["SaaS", "B2B", "enterprise", "startup", "founder", "CEO", "CTO", "software company"],
    "agencies": ["agency", "marketing agency", "design agency", "consultant", "freelancer", "client work"],
    "ecommerce": ["ecommerce", "shopify", "amazon seller", "dropshipping", "inventory", "fulfillment"],
    "developers": ["developer", "engineer", "devops", "API", "programming", "software development"],
}

# Pain point signals (buying intent)
PAIN_SIGNALS = [
    "I wish there was",
    "I'd pay for",
    "shut up and take my money",
    "is there a tool",
    "looking for a solution",
    "so frustrating",
    "waste so much time",
    "hate doing this manually",
    "anyone know a tool",
    "willing to pay",
    "need a better way",
    "current solution sucks",
    "can't find anything",
    "would save me hours",
    "tired of",
    "there has to be a better way",
    "manual process",
    "spreadsheet hell",
    "pain point",
    "bottleneck",
]

# Subreddits to monitor (high-value audiences)
SUBREDDITS = [
    "entrepreneur",
    "startups", 
    "SaaS",
    "smallbusiness",
    "Bookkeeping",
    "realestate",
    "freelance",
    "webdev",
    "devops",
    "sysadmin",
    "marketing",
    "digital_marketing",
    "ecommerce",
    "shopify",
    "lawfirm",
    "medicine",
    "healthcare",
    "accounting",
    "consulting",
    "agency",
]

# Hacker News settings
HN_STORIES_TO_CHECK = 100  # Top/new stories to scan
HN_MIN_COMMENTS = 5  # Minimum comments to consider

# Output settings
OUTPUT_DIR = "results"
