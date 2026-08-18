"""
generate_dataset.py
--------------------
Builds a labeled spam/ham email dataset from templates + randomized fillers.
This runs fully offline (no internet needed) and produces a realistically
varied dataset by combining many subject/body templates across categories
with randomized names, companies, amounts, links, and phrasing.

Run:
    python generate_dataset.py

Output:
    dataset.csv  (columns: label, subject, body, text)
"""

import csv
import random
import os

random.seed(42)

FIRST_NAMES = ["Alex", "Priya", "Daniel", "Mei", "Carlos", "Fatima", "John",
               "Sofia", "Ahmed", "Emma", "Ravi", "Grace", "Liam", "Ana",
               "Kevin", "Nina", "Omar", "Julia", "Ben", "Zara"]
LAST_NAMES = ["Turner", "Sharma", "Kim", "Rossi", "Mueller", "Chen", "Patel",
              "Garcia", "Novak", "Singh", "Brown", "Ivanov", "Lopez", "Nguyen"]
COMPANIES = ["Acme Corp", "Nova Analytics", "BrightPath Studio", "Quanta Labs",
             "Vertex Solutions", "Riverside Consulting", "Halcyon Media",
             "Skyline Retail", "Northwind Traders", "Bluepeak Software"]
BANKS = ["Chase", "Wells Fargo", "HSBC", "Citibank", "Barclays", "PNC Bank"]
PRODUCTS = ["iPhone 16 Pro", "PlayStation 5", "MacBook Air", "Rolex Watch",
            "Amazon Gift Card", "Samsung 4K TV", "Nintendo Switch"]

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_link():
    domains = ["secure-verify-account.info", "claim-reward-now.biz", "bit-ly-secure.co",
               "login-alert-update.net", "prize-center-24.com", "track-parcel-fast.xyz"]
    return f"http://{random.choice(domains)}/{random.randint(1000,9999)}"

def rand_amount():
    return f"${random.randint(500, 250000):,}"

def rand_percent():
    return f"{random.choice([50,60,70,75,80,90])}%"

# ---------------------------------------------------------------------------
# SPAM TEMPLATES  (category, subject_templates, body_templates)
# ---------------------------------------------------------------------------
SPAM_CATEGORIES = [
    # Lottery / prize scams
    {
        "subjects": [
            "CONGRATULATIONS! You've WON {amount}!!!",
            "You are today's LUCKY WINNER - claim now",
            "URGENT: Your prize of {amount} expires today",
            "Winner Notification: Ref #{ref}",
        ],
        "bodies": [
            "Dear Winner, we are pleased to inform you that your email address has won "
            "{amount} in the International Online Lottery. To claim your prize, click here: "
            "{link} and provide your full name, address and bank details within 24 hours "
            "or your prize will be forfeited. Act now, this offer will not be repeated!!!",
            "CONGRATULATIONS!!! Your ticket number has been selected to receive {amount} cash "
            "prize. This is 100% legit and guaranteed. Verify your identity immediately at "
            "{link} to release your funds. Do not tell anyone, limited winners only.",
        ],
    },
    # Phishing / account verification
    {
        "subjects": [
            "Your {bank} account has been LIMITED",
            "Action Required: Verify your account now",
            "Security Alert: unusual sign-in detected",
            "Your account will be suspended in 24 hours",
        ],
        "bodies": [
            "We detected unusual activity on your {bank} account. For your safety we have "
            "temporarily limited access. Click here to verify your identity immediately: "
            "{link} You must act within 24 hours or your account will be permanently closed.",
            "Dear Customer, your account access has been restricted due to a policy violation. "
            "Please confirm your login and password at {link} to restore full access now. "
            "Failure to verify will result in permanent suspension.",
        ],
    },
    # Pharma / health spam
    {
        "subjects": [
            "Lose {percent} body fat in 2 weeks - doctors hate this",
            "Cheap meds, no prescription needed, discreet shipping",
            "Miracle pill melts fat overnight, buy now and save {percent}",
        ],
        "bodies": [
            "Buy premium pharmaceuticals online with no prescription required! Save {percent} "
            "on all orders today only. Discreet packaging guaranteed. Order now at {link} "
            "before this limited time offer expires.",
            "Scientists shocked by this one weird trick to lose weight fast. Get your free "
            "trial bottle now, just pay shipping. Click {link} to claim your free sample "
            "before supplies run out!!!",
        ],
    },
    # Work from home / money scams
    {
        "subjects": [
            "Make {amount} per week working from home - no experience needed",
            "Earn money fast! Be your own boss starting today",
            "Financial freedom is one click away",
        ],
        "bodies": [
            "Tired of your boring 9-5 job? Earn {amount} per week from the comfort of your "
            "home with zero experience required! Just sign up at {link} and start earning "
            "today. Limited spots available, act fast!",
            "This is not a scam! Thousands of people are already earning {amount} a month "
            "with our proven system. Click {link} now to get started for FREE, no risk.",
        ],
    },
    # Tech support scam
    {
        "subjects": [
            "WARNING: Your computer is infected with a virus",
            "Microsoft Security Alert - immediate action required",
            "Your device has been compromised",
        ],
        "bodies": [
            "Our system has detected 5 viruses on your computer. Call our toll-free support "
            "line immediately or click {link} to download our security tool and remove the "
            "threat before it deletes all your files.",
            "ALERT: Suspicious activity detected on your device. Your personal data is at "
            "risk. Click {link} now to run a free scan and protect your files immediately.",
        ],
    },
    # Crypto / investment scam
    {
        "subjects": [
            "Turn {amount} into {amount2} in 7 days with crypto",
            "Exclusive investment opportunity - {percent} guaranteed return",
            "Bitcoin doubling event ends tonight",
        ],
        "bodies": [
            "Invest just {amount} today and watch it grow to {amount2} in only 7 days! Our "
            "proprietary trading bot guarantees {percent} returns. Limited slots, click {link} "
            "to secure your spot before midnight.",
            "This exclusive crypto opportunity is only available to a select few. Guaranteed "
            "{percent} return in 30 days, zero risk. Sign up now at {link} before we close "
            "registration.",
        ],
    },
    # Inheritance / prince scam
    {
        "subjects": [
            "Urgent Business Proposal - {amount} inheritance",
            "Confidential: Fund Transfer Assistance Needed",
        ],
        "bodies": [
            "I am a bank official and I have discovered a dormant account containing {amount} "
            "belonging to a deceased client with no next of kin. I require your assistance to "
            "transfer these funds. You will receive 40% of the total sum. Reply immediately "
            "and I will send further instructions to {link}.",
            "Greetings, I represent the estate of a late business magnate who left behind "
            "{amount}. As next of kin could not be located, I am reaching out to you for a "
            "confidential partnership. Contact me urgently for details.",
        ],
    },
    # Fake invoice / gift card
    {
        "subjects": [
            "Invoice #{ref} - Payment overdue, pay immediately",
            "You've received a {product} gift - claim before it expires",
            "Final Notice: outstanding balance of {amount}",
        ],
        "bodies": [
            "This is your final notice. You have an outstanding invoice of {amount}. Pay "
            "immediately at {link} to avoid legal action and additional late fees.",
            "Congratulations! You have been selected to receive a free {product}. Click "
            "{link} now and pay only a small shipping fee of $4.99 to claim your gift "
            "before it expires tonight.",
        ],
    },
]

# ---------------------------------------------------------------------------
# HAM TEMPLATES
# ---------------------------------------------------------------------------
HAM_CATEGORIES = [
    # Work meetings
    {
        "subjects": [
            "Meeting notes from today's sync",
            "Re: Q{q} planning meeting",
            "Quick question about the {company} proposal",
            "Follow up on our call yesterday",
        ],
        "bodies": [
            "Hi {name}, thanks for joining the call today. I've attached the notes from our "
            "discussion about the {company} project timeline. Let me know if I missed "
            "anything and we can go over it again tomorrow morning.",
            "Hey, just wanted to confirm we're still on for the {company} review at 2pm on "
            "Thursday. I'll send the agenda beforehand so everyone can prepare. Let me know "
            "if that time still works for you.",
        ],
    },
    # Project updates
    {
        "subjects": [
            "Project status update - week {week}",
            "Design draft ready for review",
            "Sprint {week} summary",
        ],
        "bodies": [
            "Hi team, here's a quick update on where we are with the project this week. "
            "We finished the backend integration and are on track for the deadline next "
            "Friday. Let me know if you have any questions before our next check-in.",
            "The latest design draft is ready for your review. I've made the changes we "
            "discussed last week around the navigation flow. Would love your feedback by "
            "end of day tomorrow if possible.",
        ],
    },
    # Personal / family
    {
        "subjects": [
            "Dinner this weekend?",
            "Happy birthday!",
            "Can't wait to see you next week",
            "Photos from the trip",
        ],
        "bodies": [
            "Hey, are you free for dinner this Saturday? Thinking of trying that new place "
            "downtown we talked about. Let me know what time works for you!",
            "Happy birthday! Hope you have a wonderful day. Let's catch up soon, it's been "
            "way too long. Give me a call whenever you're free this week.",
        ],
    },
    # Legit receipts / order confirmations
    {
        "subjects": [
            "Your order #{ref} has shipped",
            "Receipt for your recent purchase",
            "Order confirmation from {company}",
        ],
        "bodies": [
            "Hi {name}, your recent order has shipped and is on its way. You can track your "
            "package using the tracking number in your account dashboard. Thanks for "
            "shopping with us and let us know if you have any questions.",
            "Thanks for your purchase! Attached is the receipt for your records. If you have "
            "any issues with your order, just reply to this email and our support team will "
            "be happy to help.",
        ],
    },
    # Newsletters (legit)
    {
        "subjects": [
            "This week in tech - your weekly digest",
            "{company} Newsletter: product updates",
        ],
        "bodies": [
            "Here's what's new this week: we shipped a few small improvements to the "
            "dashboard and fixed several reported bugs. As always, thanks for being a "
            "subscriber, and feel free to reply with any feedback or feature requests.",
            "In this month's newsletter we're covering our latest product release, upcoming "
            "webinar, and a few tips from the community. Read on to learn more about what's "
            "new at {company}.",
        ],
    },
    # Scheduling / reminders
    {
        "subjects": [
            "Reminder: appointment tomorrow at {time}",
            "Your reservation is confirmed",
        ],
        "bodies": [
            "This is a friendly reminder about your appointment scheduled for tomorrow at "
            "{time}. If you need to reschedule, just reply to this email or give us a call "
            "and we'll find a time that works better.",
            "Your reservation has been confirmed for this Friday. We look forward to seeing "
            "you. If your plans change, please let us know at least 24 hours in advance.",
        ],
    },
    # Customer support replies
    {
        "subjects": [
            "Re: Support ticket #{ref}",
            "Following up on your request",
        ],
        "bodies": [
            "Hi {name}, thanks for reaching out. I looked into the issue you reported and it "
            "should be resolved now on our end. Please try again and let me know if you're "
            "still running into any trouble.",
            "Just checking in to see if the solution we suggested last week is working well "
            "for you. Happy to jump on a quick call if you'd like to go over it together.",
        ],
    },
]

# ---------------------------------------------------------------------------
# HARD / OVERLAPPING CASES - makes the dataset more realistic and prevents
# the model from relying purely on obvious keyword shortcuts.
# ---------------------------------------------------------------------------
HARD_SPAM = [
    ("Update your payment details", "We were unable to process your last payment. "
     "Please update your billing information within 3 days to avoid interruption "
     "to your service. Update here: {link}"),
    ("Your package could not be delivered", "Our courier attempted delivery today "
     "but could not access your address. Please confirm your delivery details "
     "at {link} within 48 hours or your package will be returned to sender."),
    ("Password expiring soon", "Your company email password expires in 24 hours. "
     "To keep the same password, verify your credentials now at {link}."),
    ("New voicemail received", "You have a new voicemail message (0:42). "
     "Click {link} to listen to your message before it is automatically deleted."),
]

HARD_HAM = [
    ("Your {company} order confirmation", "Thanks for your order! Your items "
     "will arrive within 3-5 business days. Save 20% on your next purchase with "
     "code THANKYOU at checkout. Questions? Reply to this email anytime."),
    ("Flash sale: 30% off ends tonight", "Hi {name}, our biggest sale of the "
     "season ends at midnight. Shop your favorites before they're gone. As "
     "always, unsubscribe anytime from the link in our footer."),
    ("Your monthly account statement is ready", "Your statement for last month "
     "is now available in your online account. Log in through our official app "
     "or website to review your recent transactions."),
    ("Reminder: verify your email to finish setup", "Hi {name}, you're almost "
     "done setting up your account. Please confirm your email address from "
     "within your account settings to unlock all features."),
    ("Win free coffee for a year - loyalty rewards", "Congrats on reaching Gold "
     "tier in our loyalty program! As a thank you, you're entered into our "
     "yearly coffee giveaway. No purchase or personal info needed to stay entered."),
]


def fill(template):
    return template.format(
        amount=rand_amount(), amount2=rand_amount(), percent=rand_percent(),
        link=rand_link(), bank=random.choice(BANKS), product=random.choice(PRODUCTS),
        ref=random.randint(10000, 99999), name=rand_name(), company=random.choice(COMPANIES),
        q=random.randint(1, 4), week=random.randint(1, 12), time=random.choice(
            ["9:00 AM", "10:30 AM", "1:00 PM", "3:15 PM", "4:45 PM"]),
    )

def generate(n_per_class=1200, n_hard_each=180):
    rows = []
    for _ in range(n_per_class):
        cat = random.choice(SPAM_CATEGORIES)
        subject = fill(random.choice(cat["subjects"]))
        body = fill(random.choice(cat["bodies"]))
        rows.append(("spam", subject, body))
    for _ in range(n_per_class):
        cat = random.choice(HAM_CATEGORIES)
        subject = fill(random.choice(cat["subjects"]))
        body = fill(random.choice(cat["bodies"]))
        rows.append(("ham", subject, body))

    # Add harder, overlapping-vocabulary examples so the model can't rely on
    # naive keyword shortcuts alone.
    for _ in range(n_hard_each):
        subj, body = random.choice(HARD_SPAM)
        rows.append(("spam", fill(subj), fill(body)))
    for _ in range(n_hard_each):
        subj, body = random.choice(HARD_HAM)
        rows.append(("ham", fill(subj), fill(body)))

    random.shuffle(rows)
    return rows

if __name__ == "__main__":
    rows = generate(n_per_class=1200)
    out_path = os.path.join(os.path.dirname(__file__), "dataset.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "subject", "body", "text"])
        for label, subject, body in rows:
            writer.writerow([label, subject, body, f"{subject}. {body}"])
    print(f"Wrote {len(rows)} rows to {out_path}")
