# Overview 
The purpose of this repository is a pipeline for YouTube video analysis and specifically fact-check. Videos can have transcripts retrieved or generated using Whisper with a flag. There are also prompts in progress for analysis of the videos. Currently the only prompt is for unverifiable or potentially misleading facts. Eventually the goal is to have a fact check pipeline and other pipelines for analyzing other elements of transcripts. 

# Open Issues
- Develop some sort of opinionation/bias measure and way to display it
- Add diarization -> sometimes the videos play clips within them and that makes the transcript nonsensical without diarization
    - Even with diarization, sometimes speakers themselves read a section of text they are quoting: it'd be nice to capture that they're quoting someone else in those scenarios
- Connect to search tool (similar to stochasticity) for fact checking 
    - Create UX to present identified potentially misleading or false facts and then give option to investigate further
- Develop a fact checking pipeline 
    - Add a reliable way to find relevant facts from transcript
    - Add a way to search for each of the facts
        - Currently thinking of doing transcript->list of facts->formulate search queries->search
        - This is a lot of steps though so I'll try transcripts->formulate search queries, skipping list of facts at some point
    - Many of these facts are so complicated lol 
    - Display in UX
- Possibly return a list of related articles from other news sources
- Utilize video title
- Add error telemetry


## Stretch Goals or Low Priority
- Add channel analysis 
- Add graph-based visualization (ex: comparisons on factors such as opinions per minute, political lean, misleading facts per 1000 words)
- Basic visualization around custom prompts 
- Add support for longer videos, maybe by breaking up the video
- UX for inputting youtube video link and getting information back 
    - UX for processing multiple videos (such as multiple videos from one channel)
    - UX to visualize results from query / video analysis 
- Currently YouTube transcripts are not cached, potential for bottleneck there due to YouTube API limits
- Currently targeting negative attacks, but could also think about pieces that defend a position or person  

## Bugs 
- Issues with initial package install (mentioned in pyproject.toml)
- Sometimes transcripts don't download the first time and need to be re-run (potentially fixed with switching to something like yt-dlc instead of yt-dlp?)

## Closed Bugs
- Fixed occassional segfault crash by setting cache_discovery to false in youtube API object config

## Completed
&check; Ability to enter a link and run the processing pipeline 

&check; Add support for downloading youtube video audio automatically

&check; Local caching for transcript retrieval and for video MP3

&check; Separate functions into different files by function (maybe helper, main, and transcript acquisition?)

&check; Have some form of web UX 

&check; Consider figuring out some UX for connecting overarching claims to the facts that are being presented

&check; Limit to reject videos over 15 minutes

&check; Split each type of analysis into its own flow

&check; Added caching for GPT output

&check; Add a bias and opinionation flow that looks for negative claims that are not backed up 

&check; Option to use YouTube transcript if it exists for video (as opposed to using Whisper)

&check; Redis support for caching and locking

&check; Host website 

&check; Custom prompt support

&check; Start deleting audio once done with it

&check; Add way to prevent multiple clicks from causing multiple requests

&check; Avoid version overlapping response when response is long

&check; When response JSON can't be decoded, print the raw JSON on the page instead of crashing

&check; Add text streaming for GPT results

&check; Longer transcripts and parallelized transcript processing (videos up to 1 hour)

## Identifying Trustworthiness of a News Piece Notes
The overarching goal of this system is to be able to find a measure of quality for news pieces and essays. In my view there are two types of good news pieces. The first is a news piece that transmits information about an event in a way that represents both sides (if two sides exist). The second is a news piece that has a "thesis" it is attempting to convey about a situation or event. Examples of this sort of news piece would be ones that are talking about a new piece of legislation and are advocating for or against it. 

The challenge comes from identifying news pieces that are more interested in presenting a perspective than in fairly representing multiple sides of an issue. These pieces come with a viewpoint pre-conceived and then either present the facts purposely in a way that leaves out other relevant factors or purposely deceive consumers with false facts. If a clear false fact is encountered such as a statistic, it can sometimes be trivial to do a search and identify it. However there are a few challenges that need to be overcome in this realm. 

One major challenge is that presenters in many cases simply can avoid facts and figures or use ones that are too vague to check. If a presenter says "this new legislation increases violent crime." It's technically a claim of fact, but we need to identify as an "opinion" because it's not something that can actually be verified. But what if they used other facts or data before that claim which back it up? Where is the line here? The line between "this connection is obvious, it doesn't need to be explained" and "this connection is just an opinion" is a tough one to explain or quantify.

Maybe logical fallacies is what I'm looking for? False facts, conjured opinions, and logical fallacies? Dog whistles are also very challenging. Often the video doesn't say anything substantive on the surface, but you have to read between the lines. Also we're looking for effect on the viewer - for example if a presenter is talking about something random but drops a line about ineffective leadership, then that's an influence on viewers even though there were no arguments and no facts and that line may not be a part of a "main" argument from the presenter at all. 

Some things that [The Disinformation Index](https://www.disinformationindex.org/country-studies/2022-12-16-disinformation-risk-assessment-the-online-news-market-in-the-united-states/) uses are "article bias" and "senational language." They also talk about language that "demeans", "belittles" or "otherwise targets" individuals, groups, or institutions. The values they measure by are listed as bias, negative targeting, out-group inferiority, sensational language, sensational visuals, sources, attribution, headline accuracy, lede present (and whether it's fact-based), and byline information. One clear weakness that the TDI has is that its measures are inherently qualitative. Their method is to have three reviewers look at each article and answer questions about those measures. 

Article on [linguistic differences between real and fake news](https://arxiv.org/abs/1703.09398). One of the things the discusses is [central versus peripheral persuasion (summary)](https://prevention.nd.gov/files/bingedrinking/ELM%20-%20Australia.pdf) which is called the "Elaboration Likelihood Model" (ELM). ELM lines up with the intuition that articles that are higher on heuristics or hand-waving are likely to be less trustworthy and that articles that contain specific facts (assuming they're true facts) are more likely to be useful.  