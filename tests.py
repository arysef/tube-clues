import json
import unittest

json_str = """
{
  "overarching_claims": [
    {
      "claim": "The Project for Awesome (P4A) is a yearly event that raises money for charities with community involvement and engagement through videos, voting, and a live stream.",
      "supporting_facts": [
        {
          "summary": "P4A is a yearly event that raises funds for various charities and involves public participation through video submissions and voting.",
          "sources": [
            "Since 2007, we have been doing a yearly thing called the Project for Awesome.",
            "You can and should make a video promoting your favorite charity, and then you can submit that video to projectforawesome.com",
            "Between January 30 and February 13, you can vote for charities featured in videos at projectforawesome.com",
            "A portion of the money that we raise during the P4A will go to the charities voted on."
          ]
        }
      ],
      "supporting_opinions": [
        {
          "summary": "The P4A event is an essential and enjoyable part of the organizers' lives and has a positive impact on charities.",
          "sources": [
            "The Project for Awesome is one of the most special and wonderful things in my life.",
            "It is wonderful. It is also very fun.",
            "Project for Awesome grants tend to be like 20-30 thousand dollars, so it can be a pretty big deal for a lot of organizations."
          ]
        }
      ]
    },
    {
      "claim": "Changes made to the P4A this year aim to simplify the process for both the organizers and participants while maintaining the event's core activities.",
      "supporting_facts": [
        {
          "summary": "For simplicity and operational reasons, the P4A will have a unified fundraising pool, reduced live stream hours, and an improved checkout process for perks.",
          "sources": [
            "But this year, since the last twelve months have been pretty weird, we're going to change some things and almost all those changes are just about simplifying, especially for the people who work on the Project for Awesome behind the scenes.",
            "So this year's Project for Awesome, all the money from all of the time during the P4A will be pooled together.",
            "We're not going to stream for all 48 hours just so that everybody on the team can have some downtime.",
            "Tiltify has introduced a new feature where you can actually, like, shopping cart up your perks."
          ]
        }
      ],
      "supporting_opinions": [
        {
          "summary": "The organizers believe these changes to simplify the P4A are necessary and will be beneficial while acknowledging possible downsides such as reduced fun from the meta gaming aspect.",
          "sources": [
            "I think that the first half-second half thing is a little confusing for people who are new.",
            "We're also doing a thing this year where in addition to having the digital download bundle, we're going to have the physical perk bundle, which is going to be a bunch of stuff, but you can get all of it for way cheaper."
          ]
        }
      ]
    },
    {
      "claim": "The effort made by the project team for the P4A is immense, and the changes are aimed to reduce the burden on them and on the organizers.",
      "supporting_facts": [
        {
          "summary": "The project team puts in a significant amount of work to make P4A successful, and the changes are intended to ease their workload.",
          "sources": [
            "We're just trying to take a little bit of lift off of them and also off of ourselves.",
            "There's a lot of people who work super hard and we're just trying to take a little bit of lift off of them and also off of ourselves."
          ]
        }
      ],
      "supporting_opinions": [
        {
          "summary": "There is a deep sense of gratitude for the team that works behind the scenes, and the changes are regarded as a way to express appreciation for their efforts.",
          "sources": [
            "I am just so grateful for all the people who work really hard to make the Project for Awesome happen behind the scenes."
          ]
        }
      ]
    }
  ]
}
"""
class Test(unittest.TestCase):
    def test_name_test_json(self):
        print(json.loads(json_str))

    # def test_empty_list(self):
    #     self.assertEqual(split_strings([]), [])

    # def test_single_string(self):
    #     self.assertEqual(split_strings(["Hello"], 10), [["Hello"]])

    # def test_single_long_string(self):
    #     self.assertEqual(split_strings(["Hello, world!"], 5), [["Hello"], [", wor"], ["ld!"]])

    # def test_multiple_short_strings(self):
    #     self.assertEqual(split_strings(["One", "Two", "Three"], 10), [["One", "Two"], ["Three"]])

    # def test_multiple_mixed_strings(self):
    #     self.assertEqual(split_strings(["One", "Two", "Three", "Four, five, six"], 7), [['One', 'Two'], ['Three'], ['Four, f'], ['ive, si'], ['x']])

    # def test_line_breaks(self):
    #     self.assertEqual(split_strings(["One\nTwo\nThree\nFour"], 6), [['One\nTw'], ['o\nThre'], ['e\nFour']])


if __name__ == '__main__':
    unittest.main()