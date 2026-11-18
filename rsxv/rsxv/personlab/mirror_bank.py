"""PERSONLAB §7d B: the invented phrase bank for the public mirror lab persons.

Every text here was written for the lab; none is taken from any dataset or person. Each entry is
(statement, current state, desired state) for one problem type and one profile level.
"""
from __future__ import annotations

TYPES = ("job crisis", "breakup with partner", "problems with friends", "academic pressure")

BANK = {
    "job crisis": {
        "environment": [
            ("I work in a busy open-plan office", "The office feels loud all day", "A quiet corner for focused work"),
            ("My team was reorganised this season", "Unsure where I fit in the new team", "A clear place in the team"),
            ("I commute an hour each way", "The commute takes my evenings", "Evenings kept for myself"),
            ("My contract runs out this quarter", "Waiting to hear about the contract", "A plan whatever the contract says"),
        ],
        "behaviour": [
            ("I check work messages late at night", "Checks messages until midnight", "Stops checking messages after dinner"),
            ("I take on tasks nobody else wants", "Says yes to every extra task", "Says no to one extra task a week"),
            ("I skip lunch to finish reports", "Works through lunch most days", "Takes a real lunch break"),
            ("I avoid asking my manager questions", "Keeps questions to myself", "Asks one clear question in each meeting"),
        ],
        "skills": [
            ("I know how to organise a project", "Organises everything except my own week", "Plans my own week as well as a project"),
            ("I can explain technical work simply", "Rarely uses this skill in reviews", "Uses it to show my results"),
            ("I spot problems early", "Spots problems but stays silent", "Raises problems early and calmly"),
            ("I can write a clear application", "Has not updated my application in years", "An application ready to send"),
        ],
        "beliefs": [
            ("Hard work should speak for itself", "Waits to be noticed", "Shows my work as well as doing it"),
            ("A good employee never complains", "Keeps concerns unspoken", "Raises concerns as part of good work"),
            ("Changing jobs means I failed", "Sees a change as failure", "Sees a change as a choice"),
            ("Security matters more than interest", "Stays only for security", "Weighs security and interest together"),
        ],
        "identity": [
            ("I am the reliable one at work", "So reliable it overloads me", "Reliable and rested"),
            ("I am someone who builds things", "Feels like a cog, not a builder", "Builds something I value"),
            ("I am the newcomer in my field", "Feels behind the others", "A newcomer who learns openly"),
            ("I am a provider for my household", "Carries the household alone", "Shares the planning at home"),
        ],
        "mission": [
            ("I want my work to help people directly", "Far from the people the work serves", "Closer to the people the work serves"),
            ("I want to show my family a steady path", "Unsure what path I am showing", "A steady path my family can see"),
            ("I want to pass my experience on", "No time to teach anyone", "Mentors one newer colleague"),
            ("I want a career I can be proud of", "Unsure about the direction", "A direction I chose"),
        ],
    },
    "breakup with partner": {
        "environment": [
            ("I still live in the flat we shared", "Every room reminds me of the past", "A home arranged for my life now"),
            ("We share the same group of friends", "Unsure which gatherings to attend", "Gatherings I choose freely"),
            ("I relocated to this town for us", "Few people of my own here", "A few people of my own here"),
            ("My evenings are suddenly empty", "Long empty evenings", "Evenings with a simple routine"),
        ],
        "behaviour": [
            ("I look at old photos every night", "Scrolls old photos before sleep", "Puts the photos away for now"),
            ("I keep my phone close in case they write", "Checks the phone constantly", "Leaves the phone in another room at night"),
            ("I have stopped going out", "Stays in most weekends", "Goes out once at the weekend"),
            ("I replay our last conversation", "Replays it many times a day", "Notices the replay and turns to something else"),
        ],
        "skills": [
            ("I look after others well", "Looks after everyone but myself", "Looks after myself as well"),
            ("I can cook a proper meal", "Has stopped cooking for one", "Cooks one proper meal a week"),
            ("I can talk openly with close friends", "Keeps friends at a distance", "Talks with one friend each week"),
            ("I can build a fresh routine", "No routine since the change", "A small routine in place"),
        ],
        "beliefs": [
            ("I need a partner to feel complete", "Feels incomplete alone", "Feels whole on my own"),
            ("The ending was all my fault", "Takes all the blame", "Sees both sides of the ending"),
            ("I will not find someone like that again", "Expects to stay alone", "Open to what comes later"),
            ("Showing sadness is weak", "Hides the sadness", "Lets the sadness be seen by a friend"),
        ],
        "identity": [
            ("I was half of a couple for years", "Unsure who I am alone", "Knows who I am on my own"),
            ("I am a loyal person", "Loyal to someone who left", "Loyal to myself as well"),
            ("I am someone who gives a lot", "Gave until nothing was left", "Gives and also receives"),
            ("I am a hopeful person", "Hope has gone quiet", "Hope returning in small ways"),
        ],
        "mission": [
            ("I want a home full of warmth", "The home feels cold", "A warm home of my own making"),
            ("I want my friends to see me thrive", "Friends see me struggling", "Friends see me growing again"),
            ("I want to build a family one day", "That future feels far away", "That future feels possible"),
            ("Kindness is the example I hope to give", "Has no energy for kindness", "Kind to others and to myself"),
        ],
    },
    "problems with friends": {
        "environment": [
            ("My friends meet at the same cafe every week", "No longer invited to the cafe", "Welcome at gatherings again"),
            ("Our group chat is very active", "Silent in the group chat", "Comfortable in the group chat"),
            ("I share a house with two friends", "Tension in the shared kitchen", "A calm shared house"),
            ("Most of my friends live nearby", "Avoids the streets where they live", "Walks freely in the neighbourhood"),
        ],
        "behaviour": [
            ("I keep quiet when something bothers me", "Stays quiet and then withdraws", "Says what bothers me early"),
            ("I cancel plans at the last minute", "Cancels most plans", "Keeps the plans I make"),
            ("I reread messages looking for hidden meaning", "Rereads every message", "Reads messages once and asks if unsure"),
            ("I always organise the group outings", "Organises everything alone", "Shares the organising"),
        ],
        "skills": [
            ("I am a good listener", "Listens but never speaks up", "Listens and also speaks up"),
            ("I can make people laugh", "Uses jokes to avoid hard topics", "Uses humour and also talks seriously"),
            ("I can apologise when I am wrong", "Apologises even when not wrong", "Apologises only when it fits"),
            ("I can plan a good evening out", "Plans for others only", "Plans an evening I enjoy too"),
        ],
        "beliefs": [
            ("Good friends should know what I need", "Expects friends to guess", "Tells friends what I need"),
            ("Conflict ends friendships", "Avoids any disagreement", "Sees disagreement as normal"),
            ("I have to earn my place in the group", "Works to be accepted", "Feels accepted as I am"),
            ("Old friends are the only true friends", "Closed to new people", "Open to new friends as well"),
        ],
        "identity": [
            ("I am the peacemaker in my group", "Keeps the peace at my own cost", "Keeps the peace and my own voice"),
            ("I am an outsider in most groups", "Feels on the edge of the group", "Feels part of a group"),
            ("I am a loyal friend", "Loyal but unheard", "Loyal and heard"),
            ("I am the one people call for help", "Called for help but not for fun", "Called for help and for fun"),
        ],
        "mission": [
            ("I want a circle of people I can trust", "Unsure whom to trust", "A few people I trust"),
            ("I want friendships that last for life", "Friendships feel fragile", "Friendships that weather a disagreement"),
            ("I want to make others feel included", "Feels excluded myself", "Includes others and feels included"),
            ("I want a community around me", "Feels alone in the town", "A small community around me"),
        ],
    },
    "academic pressure": {
        "environment": [
            ("I study in a small shared room", "No quiet place to study", "A quiet place to study"),
            ("My exams fall within one fortnight", "Everything due at once", "A schedule that spreads the load"),
            ("My course is far from my family", "Far from support at home", "Support close by as well"),
            ("The library closes early on weekends", "Nowhere to work on weekends", "A weekend place to work"),
        ],
        "behaviour": [
            ("I stay up late before every deadline", "Works through the night before deadlines", "Finishes the day before a deadline"),
            ("I put off starting large assignments", "Starts large assignments late", "Starts with a small step early"),
            ("I compare my grades with everyone", "Compares grades all the time", "Tracks my own progress"),
            ("I skip meals during exam weeks", "Forgets to eat during exams", "Regular meals in exam weeks"),
        ],
        "skills": [
            ("I can memorise material quickly", "Memorises but forgets after the exam", "Learns material that stays"),
            ("I can write well when I start", "Writes well but starts late", "Starts early and writes well"),
            ("I help classmates readily", "Helps others before my own work", "Helps others after my own work"),
            ("I can make a study timetable", "Makes timetables but does not follow them", "Follows a simple timetable"),
        ],
        "beliefs": [
            ("Anything below top marks is failure", "Sees a good mark as failure", "Sees a good mark as good"),
            ("Resting means falling behind", "Feels guilty when resting", "Sees rest as part of studying"),
            ("Asking for help shows weakness", "Never asks tutors", "Asks a tutor when stuck"),
            ("My worth depends on my results", "Results decide my mood", "Worth that does not depend on results"),
        ],
        "identity": [
            ("I am the clever one in my family", "Must never disappoint the family", "Clever and allowed to struggle"),
            ("I am a first-generation student", "Feels out of place on campus", "Belongs on campus"),
            ("Hard work is my trademark", "Works hard without direction", "Works hard with direction"),
            ("I am a curious learner", "Curiosity buried under deadlines", "Curiosity back in my studies"),
        ],
        "mission": [
            ("I want to make my parents proud", "Studies only for my parents", "Studies for myself and my parents"),
            ("I want a career that helps others", "Lost sight of why I study", "Clear about why I study"),
            ("I hope to graduate first in my family", "Doubts I will finish", "On track to finish"),
            ("I want to teach one day", "Teaching feels far away", "Takes one step toward teaching"),
        ],
    },
}

DETAILS = {
    "job crisis": {"where": ["at the office", "on the train to work", "at my desk at home"],
                   "when": ["on Monday mornings", "late in the evening", "before each review"],
                   "detail": ["for the past few months", "since the reorganisation", "most weeks"]},
    "breakup with partner": {"where": ["at home", "in the kitchen we shared", "in the park nearby"],
                             "when": ["in the evenings", "at weekends", "just before sleep"],
                             "detail": ["since the spring", "for several weeks now", "most days"]},
    "problems with friends": {"where": ["at the cafe", "in the group chat", "at shared dinners"],
                              "when": ["at weekends", "after work", "on birthdays"],
                              "detail": ["since the argument", "for a few months", "more often lately"]},
    "academic pressure": {"where": ["in the library", "in my room", "in lectures"],
                          "when": ["before deadlines", "in exam weeks", "late at night"],
                          "detail": ["this whole term", "since the first exams", "every week"]},
}

SIGNALS = {"load": "a lot to carry at once", "loss": "something important has ended",
           "conflict": "a disagreement that is still open", "change": "a change that is still settling",
           "other": "something else is weighing on them"}
