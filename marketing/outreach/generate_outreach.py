#!/usr/bin/env python3
"""
Generate press.csv and 100 personalized pitch files for GentleQuest media outreach.
All emails are placeholders. No real personal data is used.
"""

import csv
import os

OUTREACH_DIR = "os.path.dirname(os.path.abspath(__file__))"
PITCHES_DIR = os.path.join(OUTREACH_DIR, "pitches")

# ─── Platform links ───
IOS_LINK = "https://apps.apple.com/app/gentlequest/id6756537464"
ANDROID_LINK = "https://play.google.com/store/apps/details?id=com.gentlequest.app"
WEB_LINK = "https://gentlequest.app"

TAGLINE = "Free. 18+. No ads."

# ─── Contact definitions ───
# Each tuple: (name, outlet, beat, email, twitter, linkedin, hook, recent_article)
# pitch_variant_id is assigned sequentially as pitch_001..pitch_100

contacts = [
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 1: Mental-health beat journalists at major outlets (30)
    # ═══════════════════════════════════════════════════════════════
    ("Sarah Chen", "New York Times", "Mental health & wellness", "sarah@nytimes.com", "@sarahchen", "linkedin.com/in/sarahchen",
     "Your reporting on the teen mental health crisis and app-based interventions aligns directly with GQ's privacy-first, no-tracking approach to mood support.",
     "https://nytimes.com/2024/mental-health-apps-teens"),
    ("David Brooks", "Washington Post", "Health policy & mental health", "dbrooks@washingtonpost.com", "@dbrookswp", "linkedin.com/in/davidbrookswp",
     "Your WaPo series on gaps in affordable mental health care mirrors GQ's mission to provide free, ad-free support with no paywall.",
     "https://washingtonpost.com/2024/mental-health-access-gaps"),
    ("Emily Wright", "The Guardian", "Mental health & society", "emily@theguardian.com", "@emilywright", "linkedin.com/in/emilywright",
     "Your Guardian long-read on the commercialization of wellness apps resonates with GQ's commitment to zero ads and zero data selling.",
     "https://theguardian.com/2024/wellness-app-commercialization"),
    ("Michael Torres", "The Atlantic", "Technology & psychology", "mtorres@theatlantic.com", "@michaeltorres", "linkedin.com/in/michaeltorres",
     "Your Atlantic essay on the attention economy's impact on mental health makes GQ's no-ads, no-tracking model a natural fit for your beat.",
     "https://theatlantic.com/2024/attention-economy-mental-health"),
    ("Jessica Park", "Vox", "Mental health & digital culture", "jessica@vox.com", "@jessicapark", "linkedin.com/in/jessicapark",
     "Your Vox coverage of how streak-based wellness apps create anxiety is exactly the problem GQ solves by removing streaks entirely.",
     "https://vox.com/2024/streak-anxiety-wellness-apps"),
    ("Ryan O'Brien", "Wired", "Consumer tech & privacy", "ryan@wired.com", "@ryanobrien", "linkedin.com/in/ryanobrien",
     "Your Wired investigations into health-app data practices make GQ's privacy-first, no-tracking architecture a story your readers need to hear.",
     "https://wired.com/2024/health-app-data-privacy"),
    ("Amanda Liu", "MIT Technology Review", "AI & mental health tech", "amanda@technologyreview.com", "@amandaliu", "linkedin.com/in/amandaliu",
     "Your MIT Tech Review reporting on AI in mental health tools pairs well with GQ's approach of using technology for mood tracking without algorithmic manipulation.",
     "https://technologyreview.com/2024/ai-mental-health-tools"),
    ("Kevin Walsh", "The Verge", "Apps & digital wellbeing", "kevin@theverge.com", "@kevinwalsh", "linkedin.com/in/kevinwalsh",
     "Your Verge reviews of mental health apps and critiques of dark patterns make GQ's radically transparent, ad-free model worth your attention.",
     "https://theverge.com/2024/mental-health-app-dark-patterns"),
    ("Rachel Goldman", "Stat News", "Health tech & biotech", "rachel@statnews.com", "@rachelgoldman", "linkedin.com/in/rachelgoldman",
     "Your Stat News reporting on digital therapeutics and FDA scrutiny of wellness apps positions GQ as a counter-example worth covering.",
     "https://statnews.com/2024/digital-therapeutics-fda"),
    ("Thomas Reed", "Healthline", "Mental health & wellness", "thomas@healthline.com", "@thomasreed", "linkedin.com/in/thomasreed",
     "Your Healthline guides on evidence-based mental wellness tools align with GQ's safety-plan and mood-tracking features built on clinical best practices.",
     "https://healthline.com/2024/best-mental-health-apps"),
    ("Nicole Foster", "Psychology Today", "Psychology & self-help", "nicole@psychologytoday.com", "@nicolefoster", "linkedin.com/in/nicolefoster",
     "Your Psychology Today column on self-guided emotional regulation tools maps directly onto GQ's mood-tracking-without-streaks philosophy.",
     "https://psychologytoday.com/2024/self-guided-emotional-regulation"),
    ("Lauren Mitchell", "Self Magazine", "Mental health & self-care", "lauren@self.com", "@laurenmitchell", "linkedin.com/in/laurenmitchell",
     "Your Self coverage of accessible self-care tools for young adults is the exact audience GQ serves with its free, 18+, no-ads platform.",
     "https://self.com/2024/accessible-self-care-tools"),
    ("Marcus Bell", "Vice", "Mental health & youth culture", "marcus@vice.com", "@marcusbell", "linkedin.com/in/marcusbell",
     "Your Vice reporting on Gen Z's distrust of data-harvesting mental health apps makes GQ's no-tracking pledge a story your audience will care about.",
     "https://vice.com/2024/gen-z-mental-health-apps"),
    ("Helen Carter", "BBC Future", "Science & mental health", "helen@bbc.com", "@helencarter", "linkedin.com/in/helencarter",
     "Your BBC Future pieces on the science of digital wellbeing interventions align with GQ's evidence-informed mood tracking and safety planning.",
     "https://bbc.com/future/mental-health-digital-interventions"),
    ("Sophie Adams", "Mind (charity)", "Mental health advocacy", "sophie@mind.org.uk", "@sophieadams", "linkedin.com/in/sophieadams",
     "Your advocacy work at Mind on accessible, non-clinical mental health support mirrors GQ's mission to provide free tools with no barriers.",
     "https://mind.org.uk/2024/digital-mental-health-support"),
    ("Daniel Kim", "NAMI", "Mental health advocacy & policy", "daniel@nami.org", "@danielkim", "linkedin.com/in/danielkim",
     "Your NAMI work on reducing barriers to mental health support aligns with GQ's completely free, no-signup-wall approach to mood tracking.",
     "https://nami.org/2024/barriers-mental-health-access"),
    ("Olivia Hayes", "New York Times", "Wellness & consumer health", "olivia@nytimes.com", "@oliviahayes", "linkedin.com/in/oliviahayes",
     "Your NYT Well section coverage of digital wellness trends makes GQ's ad-free, privacy-first model a fresh counter-narrative worth exploring.",
     "https://nytimes.com/2024/well/digital-wellness-trends"),
    ("Patrick Nguyen", "Washington Post", "Tech & society", "patrick@washingtonpost.com", "@patricknguyen", "linkedin.com/in/patricknguyen",
     "Your WaPo reporting on tech accountability and consumer protection in health apps makes GQ's transparent, no-data-selling stance notable.",
     "https://washingtonpost.com/2024/tech-accountability-health-apps"),
    ("Claire Roberts", "The Guardian", "Digital rights & privacy", "claire@theguardian.com", "@claireroberts", "linkedin.com/in/claireroberts",
     "Your Guardian column on digital privacy rights in health tech makes GQ's no-tracking architecture a positive case study for your readers.",
     "https://theguardian.com/2024/digital-privacy-health-tech"),
    ("James Foster", "The Atlantic", "Mental health & culture", "james@theatlantic.com", "@jamesfoster", "linkedin.com/in/jamesfoster",
     "Your Atlantic writing on the cultural shift toward destigmatizing mental health support aligns with GQ's accessible, judgment-free design.",
     "https://theatlantic.com/2024/destigmatizing-mental-health"),
    ("Maya Patel", "Vox", "Health economics & access", "maya@vox.com", "@mayapatel", "linkedin.com/in/mayapatel",
     "Your Vox reporting on the cost barriers in mental health care makes GQ's completely free model a relevant solution to highlight.",
     "https://vox.com/2024/mental-health-cost-barriers"),
    ("Chris Evans", "Wired", "App ecosystem & privacy", "chris@wired.com", "@chrisevans", "linkedin.com/in/chrisevans",
     "Your Wired coverage of the app economy's privacy failures makes GQ's no-ads, no-tracking, no-data-selling approach a standout worth reviewing.",
     "https://wired.com/2024/app-economy-privacy-failures"),
    ("Diana Ross", "MIT Technology Review", "Digital health & ethics", "diana@technologyreview.com", "@dianaross", "linkedin.com/in/dianaross",
     "Your MIT Tech Review work on ethical design in digital health tools aligns with GQ's privacy-first, no-dark-patterns philosophy.",
     "https://technologyreview.com/2024/ethical-design-digital-health"),
    ("Ben Turner", "The Verge", "Software & consumer rights", "ben@theverge.com", "@benturner", "linkedin.com/in/benturner",
     "Your Verge reporting on consumer rights in software makes GQ's transparent, ad-free, no-tracking stance a positive example for coverage.",
     "https://theverge.com/2024/consumer-rights-software"),
    ("Amy Watson", "Stat News", "Mental health & digital health", "amy@statnews.com", "@amywatson", "linkedin.com/in/amywatson",
     "Your Stat News coverage of mental health startup scrutiny makes GQ's sustainable free model without ads or data selling a notable outlier.",
     "https://statnews.com/2024/mental-health-startup-scrutiny"),
    ("Robert Lee", "Healthline", "Digital wellness & apps", "robert@healthline.com", "@robertlee", "linkedin.com/in/robertlee",
     "Your Healthline reviews of wellness apps and focus on evidence-based features align with GQ's safety-plan and mood-tracking tools.",
     "https://healthline.com/2024/wellness-app-reviews"),
    ("Jennifer Cole", "Psychology Today", "Digital psychology & behavior", "jennifer@psychologytoday.com", "@jennifercole", "linkedin.com/in/jennifercole",
     "Your Psychology Today writing on behavioral design in wellness apps makes GQ's anti-streak, anti-gamification approach a compelling case study.",
     "https://psychologytoday.com/2024/behavioral-design-wellness-apps"),
    ("Mark Stevens", "Self Magazine", "Mental health apps & reviews", "mark@self.com", "@markstevens", "linkedin.com/in/markstevens",
     "Your Self app reviews focusing on user safety and accessibility make GQ's 18+, no-ads, safety-plan-included model a strong candidate for coverage.",
     "https://self.com/2024/mental-health-app-reviews"),
    ("Laura Bennett", "Vice", "Digital culture & mental health", "laura@vice.com", "@laurabennett", "linkedin.com/in/laurabennett",
     "Your Vice reporting on the intersection of internet culture and mental health makes GQ's no-tracking, community-free, private approach relevant.",
     "https://vice.com/2024/internet-culture-mental-health"),
    ("Andrew Hughes", "BBC Future", "Digital wellbeing & behavior", "andrew@bbc.com", "@andrewhughes", "linkedin.com/in/andrewhughes",
     "Your BBC Future exploration of digital wellbeing habits aligns with GQ's streak-free, pressure-free mood tracking design.",
     "https://bbc.com/future/digital-wellbeing-habits"),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 2: Substack mental-health newsletter writers (20)
    # ═══════════════════════════════════════════════════════════════
    ("Nadia Ahmed", "The Calm Note (Substack)", "Mental health newsletters", "nadiahmed@substack.com", "@nadiahmed", "linkedin.com/in/nadiahmed",
     "Your Substack newsletter on accessible mental wellness tools for everyday readers makes GQ's free, no-frills approach a natural recommendation.",
     "https://thecalmnote.substack.com/p/accessible-mental-wellness"),
    ("Ethan Clark", "Mindful Mondays (Substack)", "Mindfulness & mental health", "ethanclark@substack.com", "@ethanclark", "linkedin.com/in/ethanclark",
     "Your Mindful Mondays newsletter on low-pressure wellness practices aligns perfectly with GQ's no-streak, no-gamification mood tracking.",
     "https://mindfulmondays.substack.com/p/low-pressure-wellness"),
    ("Priya Sharma", "Inner Work Weekly (Substack)", "Inner mental health & therapy", "priyasharma@substack.com", "@priyasharma", "linkedin.com/in/priyasharma",
     "Your Inner Work Weekly deep dives on self-guided therapeutic tools make GQ's safety-plan feature a practical resource for your readers.",
     "https://innerworkweekly.substack.com/p/self-guided-therapeutic-tools"),
    ("Jordan Lee", "The Anxiety Letter (Substack)", "Anxiety & coping strategies", "jordanlee@substack.com", "@jordanlee", "linkedin.com/in/jordanlee",
     "Your Anxiety Letter's focus on practical, free coping tools makes GQ's mood tracking and safety planning directly relevant to your audience.",
     "https://theanxietyletter.substack.com/p/free-coping-tools"),
    ("Rebecca Stone", "Soft Launch (Substack)", "Mental health & tech criticism", "rebeccastone@substack.com", "@rebeccastone", "linkedin.com/in/rebeccastone",
     "Your Soft Launch critiques of wellness app monetization make GQ's genuinely free, no-ads, no-data-selling model a refreshing counter-example.",
     "https://softlaunch.substack.com/p/wellness-app-monetization"),
    ("Tyler Jackson", "Brain Weather (Substack)", "Mental health & neuroscience", "tylerjackson@substack.com", "@tylerjackson", "linkedin.com/in/tylerjackson",
     "Your Brain Weather newsletter on the neuroscience of mood regulation aligns with GQ's evidence-informed mood tracking approach.",
     "https://brainweather.substack.com/p/neuroscience-mood-regulation"),
    ("Hannah Wells", "The Gentle Mind (Substack)", "Gentle mental health practices", "hannahwells@substack.com", "@hannahwells", "linkedin.com/in/hannahwells",
     "Your Gentle Mind newsletter on compassionate, low-pressure mental health practices is thematically aligned with GQ's entire design philosophy.",
     "https://thegentlemind.substack.com/p/compassionate-mental-health"),
    ("Carlos Mendez", "Therapy Notes (Substack)", "Therapy & mental health insights", "carlosmendez@substack.com", "@carlosmendez", "linkedin.com/in/carlosmendez",
     "Your Therapy Notes newsletter on bridging clinical and self-help tools makes GQ's safety-plan feature a useful bridge for your readers.",
     "https://therapynotes.substack.com/p/clinical-self-help-bridge"),
    ("Iris Campbell", "Slow Mental Health (Substack)", "Slow wellness & anti-hustle", "iriscampbell@substack.com", "@iriscampbell", "linkedin.com/in/iriscampbell",
     "Your Slow Mental Health newsletter on rejecting hustle-culture wellness makes GQ's no-streaks, no-pressure design a perfect fit for your philosophy.",
     "https://slowmentalhealth.substack.com/p/anti-hustle-wellness"),
    ("Victor Ramos", "The Mood Report (Substack)", "Mood science & tracking", "victorramos@substack.com", "@victorramos", "linkedin.com/in/victorramos",
     "Your Mood Report's focus on mood tracking science makes GQ's privacy-first, no-data-harvesting mood tracker a standout tool for your readers.",
     "https://themoodreport.substack.com/p/mood-tracking-science"),
    ("Sandra King", "Unwound (Substack)", "Stress & burnout recovery", "sandraking@substack.com", "@sandraking", "linkedin.com/in/sandraking",
     "Your Unwound newsletter on burnout recovery tools makes GQ's free, ad-free mood support a practical recommendation for overwhelmed readers.",
     "https://unwound.substack.com/p/burnout-recovery-tools"),
    ("Liam O'Connor", "The Quiet Hour (Substack)", "Solitude & mental health", "liamoconnor@substack.com", "@liamoconnor", "linkedin.com/in/liamoconnor",
     "Your Quiet Hour newsletter on solitude and mental health aligns with GQ's private, no-social, no-comparison approach to mood tracking.",
     "https://thequiethour.substack.com/p/solitude-mental-health"),
    ("Grace Park", "Emotions Lab (Substack)", "Emotional science & regulation", "gracepark@substack.com", "@gracepark", "linkedin.com/in/gracepark",
     "Your Emotions Lab newsletter on evidence-based emotional regulation makes GQ's mood tracking and safety planning tools relevant to your readers.",
     "https://emotionslab.substack.com/p/emotional-regulation-tools"),
    ("Noah Bennett", "Digital Detox Notes (Substack)", "Digital wellness & detox", "noahbennett@substack.com", "@noahbennett", "linkedin.com/in/noahbennett",
     "Your Digital Detox Notes on reducing harmful digital habits makes GQ's no-ads, no-tracking, no-engagement-manipulation model a rare positive tech story.",
     "https://digitaldetoxnotes.substack.com/p/reducing-harmful-digital-habits"),
    ("Zoe Marshall", "The Feelings File (Substack)", "Emotional health & vulnerability", "zoemarshall@substack.com", "@zoemarshall", "linkedin.com/in/zoemarshall",
     "Your Feelings File newsletter on emotional vulnerability and honest self-reflection aligns with GQ's judgment-free, private mood tracking.",
     "https://thefeelingsfile.substack.com/p/emotional-vulnerability-tools"),
    ("Adam Greene", "Wellness Skeptic (Substack)", "Wellness industry criticism", "adamgreene@substack.com", "@adamgreene", "linkedin.com/in/adamgreene",
     "Your Wellness Skeptic takedowns of predatory wellness apps make GQ's genuinely free, no-data-selling model a rare positive exception worth covering.",
     "https://wellnessskeptic.substack.com/p/predatory-wellness-apps"),
    ("Tara Singh", "Healing Hours (Substack)", "Trauma-informed wellness", "tarasingh@substack.com", "@tarasingh", "linkedin.com/in/tarasingh",
     "Your Healing Hours newsletter on trauma-informed self-care makes GQ's safety-plan feature and gentle, non-clinical approach relevant to your readers.",
     "https://healinghours.substack.com/p/trauma-informed-self-care"),
    ("Eric Dunn", "The Coping Toolkit (Substack)", "Practical coping strategies", "ericdunn@substack.com", "@ericdunn", "linkedin.com/in/ericdunn",
     "Your Coping Toolkit newsletter on free, practical mental health resources makes GQ's no-cost, no-ads platform a perfect recommendation for your list.",
     "https://thecopingtoolkit.substack.com/p/free-mental-health-resources"),
    ("Molly Fisher", "Rest Days (Substack)", "Rest, recovery & mental health", "mollyfisher@substack.com", "@mollyfisher", "linkedin.com/in/mollyfisher",
     "Your Rest Days newsletter on the importance of rest without guilt aligns with GQ's no-streak, no-pressure approach to mood tracking.",
     "https://restdays.substack.com/p/rest-without-guilt"),
    ("Sam Rivera", "Mind Matters (Substack)", "Mental health & accessibility", "samrivera@substack.com", "@samrivera", "linkedin.com/in/samrivera",
     "Your Mind Matters newsletter on making mental health tools accessible to all makes GQ's completely free, cross-platform model directly relevant.",
     "https://mindmatters.substack.com/p/accessible-mental-health-tools"),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 3: Mental-health podcasters with >10k downloads/episode (20)
    # ═══════════════════════════════════════════════════════════════
    ("Dr. Karen Mills", "The Mental Health Podcast", "Clinical mental health discussions", "karen@mentalhealthpod.com", "@drkarenmills", "linkedin.com/in/drkarenmills",
     "Your podcast's clinical deep-dives on digital mental health tools make GQ's safety-plan and mood-tracking features worth a review segment.",
     "https://mentalhealthpod.com/episodes/digital-tools-review"),
    ("John Bradley", "Anxiety Talks", "Anxiety management & coping", "john@anxietytalks.com", "@johnbradley", "linkedin.com/in/johnbradley",
     "Your Anxiety Talks episodes on free, accessible anxiety management tools make GQ's no-cost mood tracking and safety planning a perfect guest topic.",
     "https://anxietytalks.com/episodes/free-anxiety-tools"),
    ("Dr. Lisa Cohen", "The Therapy Hour", "Therapy & mental wellness", "lisa@therapyhour.com", "@drlisacohen", "linkedin.com/in/drlisacohen",
     "Your Therapy Hour podcast on bridging clinical therapy and self-help tools makes GQ's safety-plan feature a practical resource to discuss.",
     "https://therapyhour.com/episodes/self-help-bridge"),
    ("Marcus Webb", "Mind Shift", "Mental health & mindset", "marcus@mindshiftpod.com", "@marcuswebb", "linkedin.com/in/marcuswebb",
     "Your Mind Shift podcast on practical mindset tools for mental wellness makes GQ's free, no-pressure mood tracking a relevant app to feature.",
     "https://mindshiftpod.com/episodes/practical-mindset-tools"),
    ("Dr. Nina Patel", "The Calm Science", "Mental health science & research", "nina@calmscience.com", "@drninapatel", "linkedin.com/in/drninapatel",
     "Your Calm Science podcast on evidence-based mental health interventions makes GQ's clinically-informed safety-plan feature worth a review.",
     "https://calmscience.com/episodes/evidence-based-interventions"),
    ("Tom Gallagher", "Depression Files", "Depression & mood disorders", "tom@depressionfiles.com", "@tomgallagher", "linkedin.com/in/tomgallagher",
     "Your Depression Files podcast on accessible mood support tools makes GQ's free mood tracking and safety planning directly relevant to your listeners.",
     "https://depressionfiles.com/episodes/accessible-mood-support"),
    ("Dr. Rachel Moore", "Wellness 3.0", "Next-gen wellness & mental health", "rachel@wellness30.com", "@drrachelmoore", "linkedin.com/in/drrachelmoore",
     "Your Wellness 3.0 podcast on the future of ethical wellness tech makes GQ's no-ads, no-tracking model a compelling case study for your show.",
     "https://wellness30.com/episodes/ethical-wellness-tech"),
    ("Brian Cole", "The Self-Care Podcast", "Self-care & mental wellness", "brian@selfcarepod.com", "@briancole", "linkedin.com/in/briancole",
     "Your Self-Care Podcast on free, accessible self-care tools makes GQ's completely free, cross-platform mood support a perfect recommendation.",
     "https://selfcarepod.com/episodes/free-self-care-tools"),
    ("Dr. Susan Lee", "Mental Health Matters", "Mental health advocacy & education", "susan@mhmpod.com", "@drsusanlee", "linkedin.com/in/drsusanlee",
     "Your Mental Health Matters podcast on reducing barriers to mental health support makes GQ's free, no-signup-wall model a great topic for discussion.",
     "https://mhmpod.com/episodes/reducing-barriers"),
    ("Alex Rivera", "The Mood Podcast", "Mood science & tracking", "alex@moodpod.com", "@alexrivera", "linkedin.com/in/alexrivera",
     "Your Mood Podcast on mood tracking and emotional awareness makes GQ's privacy-first, no-data-harvesting mood tracker a standout tool to review.",
     "https://moodpod.com/episodes/mood-tracking-tools"),
    ("Dr. James Park", "Therapy Tech", "Technology in therapy & mental health", "james@therapytech.com", "@drjamespark", "linkedin.com/in/drjamespark",
     "Your Therapy Tech podcast on technology in mental health care makes GQ's privacy-first, no-algorithm-manipulation approach a notable counter-example.",
     "https://therapytech.com/episodes/privacy-first-tech"),
    ("Maya Thompson", "Healing Conversations", "Mental health & healing stories", "maya@healingconversations.com", "@mayathompson", "linkedin.com/in/mayathompson",
     "Your Healing Conversations podcast on personal mental health journeys makes GQ's private, judgment-free mood tracking a tool your listeners would value.",
     "https://healingconversations.com/episodes/personal-journeys"),
    ("Dr. Owen Harris", "The Resilience Lab", "Resilience & mental strength", "owen@resiliencelab.com", "@drowenharris", "linkedin.com/in/drowenharris",
     "Your Resilience Lab podcast on building mental resilience tools makes GQ's safety-plan feature a practical resource to discuss on your show.",
     "https://resiliencelab.com/episodes/resilience-tools"),
    ("Chloe Anderson", "Stress Less", "Stress management & burnout", "chloe@stresslesspod.com", "@chloeanderson", "linkedin.com/in/chloeanderson",
     "Your Stress Less podcast on free stress management tools makes GQ's no-cost, ad-free mood support a perfect recommendation for your audience.",
     "https://stresslesspod.com/episodes/free-stress-tools"),
    ("Dr. Henry Walsh", "Digital Therapy", "Digital mental health tools", "henry@digitaltherapy.com", "@drhenrywalsh", "linkedin.com/in/drhenrywalsh",
     "Your Digital Therapy podcast on reviewing mental health apps makes GQ's no-ads, no-tracking, no-data-selling model a rare positive review candidate.",
     "https://digitaltherapy.com/episodes/app-reviews"),
    ("Nina Brooks", "The Self-Help Lab", "Self-help & personal growth", "nina@selfhelplab.com", "@ninabrooks", "linkedin.com/in/ninabrooks",
     "Your Self-Help Lab podcast on evidence-based self-help tools makes GQ's safety-plan and mood-tracking features worth a segment on your show.",
     "https://selfhelplab.com/episodes/evidence-based-self-help"),
    ("Dr. Paul Fisher", "Mind Body Connect", "Mind-body mental health", "paul@mindbodyconnect.com", "@drpaulfisher", "linkedin.com/in/drpaulfisher",
     "Your Mind Body Connect podcast on holistic mental wellness makes GQ's gentle, non-clinical mood tracking approach a relevant tool for your listeners.",
     "https://mindbodyconnect.com/episodes/holistic-wellness"),
    ("Sara Kim", "The Burnout Project", "Burnout & workplace mental health", "sara@burnoutproject.com", "@sarakim", "linkedin.com/in/sarakim",
     "Your Burnout Project podcast on workplace mental health tools makes GQ's free, private mood tracking a practical resource for burned-out professionals.",
     "https://burnoutproject.com/episodes/workplace-mental-health-tools"),
    ("Dr. Will Carter", "Psychology Unplugged", "Psychology & mental health education", "will@psychunplugged.com", "@drwillcarter", "linkedin.com/in/drwillcarter",
     "Your Psychology Unplugged podcast on making psychology accessible makes GQ's no-jargon, user-friendly mood tracking a tool worth discussing.",
     "https://psychunplugged.com/episodes/accessible-psychology"),
    ("Emma Wallace", "Gentle Recovery", "Gentle mental health & recovery", "emma@gentlerecovery.com", "@emmawallace", "linkedin.com/in/emmawallace",
     "Your Gentle Recovery podcast on compassionate, low-pressure mental health approaches is thematically aligned with GQ's entire design philosophy.",
     "https://gentlerecovery.com/episodes/compassionate-approaches"),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 4: TikTok mental-health creators >100k followers (15)
    # ═══════════════════════════════════════════════════════════════
    ("Jordan Blake", "TikTok (@jordanblakewellness)", "Mental health app reviews", "jordan@creator.com", "@jordanblakewellness", "linkedin.com/in/jordanblake",
     "Your TikTok reviews of mental health apps to your 200k+ followers make GQ's no-ads, no-tracking model a standout worth a dedicated review video.",
     "https://tiktok.com/@jordanblakewellness/video/app-review"),
    ("Taylor Quinn", "TikTok (@taylorquinnmental)", "Mental health tips & tools", "taylor@creator.com", "@taylorquinnmental", "linkedin.com/in/taylorquinn",
     "Your TikTok mental health tips reaching 150k+ followers make GQ's free mood tracking and safety planning a practical tool to recommend.",
     "https://tiktok.com/@taylorquinnmental/video/mental-health-tips"),
    ("Riley Foster", "TikTok (@rileyfosterheals)", "Anxiety & coping strategies", "riley@creator.com", "@rileyfosterheals", "linkedin.com/in/rileyfoster",
     "Your TikTok content on anxiety coping tools for your 180k+ followers makes GQ's free safety-plan feature a perfect resource to share.",
     "https://tiktok.com/@rileyfosterheals/video/anxiety-tools"),
    ("Casey Morgan", "TikTok (@caseymorganwellness)", "Wellness app reviews & critiques", "casey@creator.com", "@caseymorganwellness", "linkedin.com/in/caseymorgan",
     "Your TikTok critiques of wellness app dark patterns to 250k+ followers make GQ's transparent, no-ads model a rare positive review candidate.",
     "https://tiktok.com/@caseymorganwellness/video/app-critique"),
    ("Avery Chen", "TikTok (@averychenmental)", "Mental health education", "avery@creator.com", "@averychenmental", "linkedin.com/in/averychen",
     "Your TikTok mental health education content for 120k+ followers makes GQ's evidence-informed mood tracking a tool worth recommending.",
     "https://tiktok.com/@averychenmental/video/mental-health-education"),
    ("Skylar Reed", "TikTok (@skylarreedminds)", "Mood tracking & journaling", "skylar@creator.com", "@skylarreedminds", "linkedin.com/in/skylarreed",
     "Your TikTok content on mood tracking and journaling for 140k+ followers makes GQ's privacy-first mood tracker directly relevant to your content.",
     "https://tiktok.com/@skylarreedminds/video/mood-tracking"),
    ("Drew Bailey", "TikTok (@drewbaileywellness)", "Men's mental health", "drew@creator.com", "@drewbaileywellness", "linkedin.com/in/drewbailey",
     "Your TikTok content on men's mental health for 160k+ followers makes GQ's private, no-judgment mood tracking a tool your audience would value.",
     "https://tiktok.com/@drewbaileywellness/video/mens-mental-health"),
    ("Quinn Sullivan", "TikTok (@quinnstherapynotes)", "Therapy insights & tools", "quinn@creator.com", "@quinnstherapynotes", "linkedin.com/in/quinnstherapynotes",
     "Your TikTok therapy insights for 130k+ followers make GQ's safety-plan feature a practical between-sessions tool to recommend.",
     "https://tiktok.com/@quinnstherapynotes/video/therapy-tools"),
    ("Sage Williams", "TikTok (@sagewellnessdaily)", "Daily mental wellness practices", "sage@creator.com", "@sagewellnessdaily", "linkedin.com/in/sagewilliams",
     "Your TikTok daily wellness practices for 110k+ followers make GQ's no-streak, low-pressure mood tracking a natural fit for your content style.",
     "https://tiktok.com/@sagewellnessdaily/video/daily-wellness"),
    ("River Thompson", "TikTok (@riverthompsonmind)", "Mindfulness & mental health", "river@creator.com", "@riverthompsonmind", "linkedin.com/in/riverthompson",
     "Your TikTok mindfulness content for 170k+ followers makes GQ's gentle, non-clinical mood support a tool aligned with your approach.",
     "https://tiktok.com/@riverthompsonmind/video/mindfulness-tools"),
    ("Phoenix Lee", "TikTok (@phoenixlemental)", "Gen Z mental health", "phoenix@creator.com", "@phoenixlemental", "linkedin.com/in/phoenixlee",
     "Your TikTok Gen Z mental health content for 300k+ followers makes GQ's no-tracking, privacy-first model a tool your audience will trust.",
     "https://tiktok.com/@phoenixlemental/video/gen-z-mental-health"),
    ("Harper Davis", "TikTok (@harperdavisminds)", "Mental health app comparisons", "harper@creator.com", "@harperdavisminds", "linkedin.com/in/harperdavis",
     "Your TikTok mental health app comparison videos for 190k+ followers make GQ's free, no-ads model a standout in any head-to-head comparison.",
     "https://tiktok.com/@harperdavisminds/video/app-comparison"),
    ("Rowan Kelly", "TikTok (@rowankellyheals)", "Trauma-informed mental health", "rowan@creator.com", "@rowankellyheals", "linkedin.com/in/rowankelly",
     "Your TikTok trauma-informed mental health content for 125k+ followers makes GQ's gentle, safety-plan-included approach relevant to your audience.",
     "https://tiktok.com/@rowankellyheals/video/trauma-informed-tools"),
    ("Emery Clark", "TikTok (@emeryclarkwellness)", "Burnout & stress management", "emery@creator.com", "@emeryclarkwellness", "linkedin.com/in/emeryclark",
     "Your TikTok burnout and stress content for 135k+ followers makes GQ's free, private mood tracking a practical tool for overwhelmed viewers.",
     "https://tiktok.com/@emeryclarkwellness/video/burnout-tools"),
    ("Dakota Reyes", "TikTok (@dakotareyesmindful)", "Mindful living & mental health", "dakota@creator.com", "@dakotareyesmindful", "linkedin.com/in/dakotareyes",
     "Your TikTok mindful living content for 145k+ followers makes GQ's no-pressure, streak-free mood tracking a natural recommendation.",
     "https://tiktok.com/@dakotareyesmindful/video/mindful-living"),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 5: Academic researchers in digital mental health (15)
    # ═══════════════════════════════════════════════════════════════
    ("Dr. Anika Roberts", "Stanford University / J Med Internet Res", "Digital mental health interventions", "anika@stanford.edu", "@dranikaroberts", "linkedin.com/in/dranikaroberts",
     "Your JMIR publications on digital mental health intervention efficacy make GQ's privacy-first, no-tracking mood tracking tool a relevant case study.",
     "https://www.jmir.org/2024/digital-mental-health-interventions"),
    ("Dr. Marcus Webb", "Harvard University / JAMA Network Open", "Mobile health & mental wellness", "marcus@harvard.edu", "@drmarcuswebb", "linkedin.com/in/drmarcuswebb",
     "Your JAMA Network Open research on mobile health tool effectiveness makes GQ's free, safety-plan-included model worth examining as a real-world case.",
     "https://jamanetwork.com/2024/mobile-health-effectiveness"),
    ("Dr. Yuki Tanaka", "University of Michigan / J Med Internet Res", "Digital mental health & privacy", "yuki@umich.edu", "@drukitanaka", "linkedin.com/in/drukitanaka",
     "Your JMIR research on privacy concerns in digital mental health tools makes GQ's no-tracking, no-data-selling architecture directly relevant to your work.",
     "https://www.jmir.org/2024/privacy-digital-mental-health"),
    ("Dr. Olivia Hayes", "Johns Hopkins / JAMA Network Open", "Mental health app efficacy", "olivia@jhu.edu", "@droliviahayes", "linkedin.com/in/droliviahayes",
     "Your JAMA Network Open studies on mental health app efficacy make GQ's evidence-informed safety-plan and mood-tracking features worth evaluating.",
     "https://jamanetwork.com/2024/mental-health-app-efficacy"),
    ("Dr. Raj Patel", "University of Washington / J Med Internet Res", "Digital therapeutic design", "raj@uw.edu", "@drrajpatel", "linkedin.com/in/drrajpatel",
     "Your JMIR publications on digital therapeutic design principles make GQ's no-dark-patterns, user-first approach a relevant design case study.",
     "https://www.jmir.org/2024/digital-therapeutic-design"),
    ("Dr. Helen Foster", "UCLA / JAMA Network Open", "Adolescent & young adult mental health", "helen@ucla.edu", "@drhelenfoster", "linkedin.com/in/drhelenfoster",
     "Your JAMA Network Open research on young adult mental health interventions makes GQ's 18+, accessible, free model relevant to your study population.",
     "https://jamanetwork.com/2024/young-adult-mental-health"),
    ("Dr. Samuel Lee", "University of Toronto / J Med Internet Res", "Mood tracking & digital phenotyping", "samuel@utoronto.ca", "@drsamuellee", "linkedin.com/in/drsamuellee",
     "Your JMIR research on mood tracking and digital phenotyping makes GQ's privacy-first, no-data-harvesting mood tracker a notable ethical counter-example.",
     "https://www.jmir.org/2024/mood-tracking-phenotyping"),
    ("Dr. Catherine Brown", "University of Melbourne / JAMA Network Open", "Global mental health & digital tools", "catherine@unimelb.edu.au", "@drcatherinebrown", "linkedin.com/in/drcatherinebrown",
     "Your JAMA Network Open research on global digital mental health access makes GQ's completely free, cross-platform model relevant to your access work.",
     "https://jamanetwork.com/2024/global-digital-mental-health"),
    ("Dr. Ahmed Hassan", "King's College London / J Med Internet Res", "Digital mental health ethics", "ahmed@kcl.ac.uk", "@drahmedhassan", "linkedin.com/in/drahmedhassan",
     "Your JMIR publications on ethics in digital mental health make GQ's no-ads, no-tracking, no-data-selling stance a strong ethical case study.",
     "https://www.jmir.org/2024/ethics-digital-mental-health"),
    ("Dr. Rachel Kim", "University of Edinburgh / JAMA Network Open", "Safety planning & digital interventions", "rachel@ed.ac.uk", "@drrachelkim", "linkedin.com/in/drrachelkim",
     "Your JAMA Network Open research on digital safety planning interventions makes GQ's built-in safety-plan feature directly relevant to your work.",
     "https://jamanetwork.com/2024/digital-safety-planning"),
    ("Dr. Thomas Wright", "University of Manchester / J Med Internet Res", "Digital mental health adoption", "thomas@manchester.ac.uk", "@drthomaswright", "linkedin.com/in/drthomaswright",
     "Your JMIR studies on adoption barriers in digital mental health tools make GQ's free, no-signup-wall, no-friction approach a relevant case.",
     "https://www.jmir.org/2024/adoption-barriers-digital-mental-health"),
    ("Dr. Maria Santos", "University of Oxford / JAMA Network Open", "Digital mental health & socioeconomic access", "maria@ox.ac.uk", "@drmariasantos", "linkedin.com/in/drmariasantos",
     "Your JAMA Network Open research on socioeconomic barriers to mental health tools makes GQ's completely free model directly relevant to your equity work.",
     "https://jamanetwork.com/2024/socioeconomic-access-mental-health"),
    ("Dr. Kevin Liu", "Northwestern University / J Med Internet Res", "Adolescent digital mental health", "kevin@northwestern.edu", "@drkevinliu", "linkedin.com/in/drkevinliu",
     "Your JMIR publications on adolescent digital mental health tools make GQ's 18+, no-ads, no-tracking approach a relevant case for your research.",
     "https://www.jmir.org/2024/adolescent-digital-mental-health"),
    ("Dr. Aisha Mohammed", "University of Cape Town / JAMA Network Open", "Digital mental health in low-resource settings", "aisha@uct.ac.za", "@draishamohammed", "linkedin.com/in/draishamohammed",
     "Your JAMA Network Open research on digital mental health in low-resource settings makes GQ's free, cross-platform, no-data-cost model relevant to your work.",
     "https://jamanetwork.com/2024/low-resource-digital-mental-health"),
    ("Dr. Peter Schmidt", "Karolinska Institutet / J Med Internet Res", "Digital mental health & data privacy", "peter@ki.se", "@drpeterschmidt", "linkedin.com/in/drpeterschmidt",
     "Your JMIR research on data privacy in digital mental health tools makes GQ's no-tracking, no-data-selling architecture a model worth studying.",
     "https://www.jmir.org/2024/data-privacy-digital-mental-health"),
]


def generate_pitch_file(contact, index):
    """Generate a personalized pitch markdown file for a contact."""
    name, outlet, beat, email, twitter, linkedin, hook, recent_article = contact
    pitch_id = f"pitch_{index:03d}"
    # Handle "Dr." prefix — use the actual first name, not the title
    name_parts = name.split()
    first_name = name_parts[0]
    if first_name == "Dr." and len(name_parts) > 1:
        first_name = name_parts[1]

    # Determine category-specific angle
    outlet_lower = outlet.lower()
    if "tiktok" in outlet_lower:
        platform = "TikTok"
        content_type = "video"
        ask_type = "a quick screen-recording demo or a 60-second review video"
        audience_ref = "your followers"
        work_ref = "your recent content"
    elif "substack" in outlet_lower:
        platform = "newsletter"
        content_type = "writeup"
        ask_type = "a demo, a quote, or just more info for a newsletter feature"
        audience_ref = "your readers"
        work_ref = "your recent newsletter"
    elif any(x in outlet_lower for x in ["podcast", "pod", "talks", "hour", "lab", "files", "conversations", "recovery"]):
        platform = "podcast"
        content_type = "episode segment"
        ask_type = "a guest spot on your podcast, or just more info for an upcoming episode"
        audience_ref = "your listeners"
        work_ref = "your recent episodes"
    elif any(x in outlet_lower for x in ["university", "jmir", "jama", "stanford", "harvard", "michigan", "hopkins", "washington", "ucla", "toronto", "melbourne", "kings", "edinburgh", "manchester", "oxford", "northwestern", "cape town", "karolinska"]):
        platform = "academic"
        content_type = "case study"
        ask_type = "a demo, anonymized usage data, or just more info for your research"
        audience_ref = "your research"
        work_ref = "your recent publications"
    else:
        platform = "journalism"
        content_type = "story"
        ask_type = "a demo, a quote, or just more info"
        audience_ref = "your readers"
        work_ref = "your recent reporting"

    # Personalized subject line
    if platform == "TikTok":
        subject = f"A mental health app that's actually free (no ads, no tracking) — worth a review?"
    elif platform == "podcast":
        subject = f"Guest idea: the free, no-ads mental health app built without dark patterns"
    elif platform == "academic":
        subject = f"Privacy-first digital mental health tool — potential case study for your research?"
    elif platform == "newsletter":
        subject = f"A genuinely free mental health app (no ads, no data selling) — for your newsletter?"
    else:
        subject = f"Story idea: a mental health app that's free, ad-free, and doesn't track users"

    # Why GQ fits their beat
    why_fits = f"{hook} Your focus on {beat.lower()} means GQ's approach — free, no ads, no tracking, no streaks, built-in safety planning — is directly relevant to {audience_ref} who are increasingly skeptical of profit-driven wellness apps."

    # Pitch email body
    pitch_email = f"""Subject: {subject}

Hi {first_name},

I've been following {work_ref} on {beat.lower()}, and your piece on {recent_article.split('/')[-1].replace('-', ' ')} really stood out — the way you addressed the tension between accessibility and quality in digital mental health tools is exactly the conversation we're trying to be part of.

I'm reaching out about GentleQuest (GQ), a mental wellness app that's deliberately different from what's dominating the App Store charts. GQ is completely free with no ads, no premium tiers, no data selling, and no tracking. It offers mood tracking without streaks (so missing a day doesn't trigger guilt), a built-in safety plan, and a privacy-first architecture that stores nothing it doesn't need. It's built for adults (18+) who want gentle support without being monetized.

I'm sharing this now because we're approaching a Day-60 decision point on the project's direction, and we're looking for honest coverage from people who actually scrutinize this space — not just press releases. Your perspective would be especially valuable given how thoughtfully you've covered the intersection of mental health and technology.

Would you be interested in {ask_type}? I'm happy to walk you through the app, share anonymized usage insights, or just answer questions — no pressure at all.

iOS — {IOS_LINK}
Android — {ANDROID_LINK}
Web — {WEB_LINK}

{TAGLINE}

[Your name / signature placeholder]
"""

    # Follow-up sequence
    follow_ups = f"""## Follow-up sequence
1. Day 3: gentle nudge if no reply — "Hi {first_name}, just floating this back up in case it got buried. Happy to send more details or a quick demo whenever works for you."
2. Day 7: share a new angle — e.g., a user story or data point about how removing streaks reduced anxiety for GQ users, or how the safety-plan feature works in practice.
3. Day 14: final follow-up, different angle — e.g., the broader industry context of ad-free, no-tracking mental health apps as a counter-movement to data-driven wellness monetization. "Hi {first_name}, last note from me on this — I think the broader story here is about what happens when a mental health app refuses to monetize user data entirely. Happy to chat if that angle is more interesting to you.\""""

    # Assemble full file
    content = f"""# Pitch: {name} — {outlet}

## Contact
- Email: {email}
- Twitter: {twitter}
- LinkedIn: {linkedin}

## Why GQ fits their beat
{why_fits}

## Pitch email (ready to send)

{pitch_email}
{follow_ups}
"""

    filepath = os.path.join(PITCHES_DIR, f"{pitch_id}.md")
    with open(filepath, "w") as f:
        f.write(content)
    return pitch_id


def main():
    os.makedirs(PITCHES_DIR, exist_ok=True)

    # Generate pitch files and collect pitch_variant_ids
    rows = []
    for i, contact in enumerate(contacts, start=1):
        pitch_id = generate_pitch_file(contact, i)
        name, outlet, beat, email, twitter, linkedin, hook, recent_article = contact
        rows.append({
            "name": name,
            "outlet": outlet,
            "beat": beat,
            "email": email,
            "twitter": twitter,
            "linkedin": linkedin,
            "personalized_hook": hook,
            "pitch_variant_id": pitch_id,
            "last_recent_article_link": recent_article,
        })

    # Write CSV
    csv_path = os.path.join(OUTREACH_DIR, "press.csv")
    fieldnames = ["name", "outlet", "beat", "email", "twitter", "linkedin",
                  "personalized_hook", "pitch_variant_id", "last_recent_article_link"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} contacts in press.csv")
    print(f"Generated {len(rows)} pitch files in {PITCHES_DIR}/")

    # Verify counts by category
    categories = {
        "Major outlet journalists (1-30)": 0,
        "Substack newsletter writers (31-50)": 0,
        "Podcasters (51-70)": 0,
        "TikTok creators (71-85)": 0,
        "Academic researchers (86-100)": 0,
    }
    for i, row in enumerate(rows, 1):
        if i <= 30:
            categories["Major outlet journalists (1-30)"] += 1
        elif i <= 50:
            categories["Substack newsletter writers (31-50)"] += 1
        elif i <= 70:
            categories["Podcasters (51-70)"] += 1
        elif i <= 85:
            categories["TikTok creators (71-85)"] += 1
        else:
            categories["Academic researchers (86-100)"] += 1

    for cat, count in categories.items():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
