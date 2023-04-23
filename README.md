# Overview 
The purpose of this repository is a pipeline for YouTube video analysis and specifically fact-check. Videos can have transcripts retrieved or generated using Whisper with a flag. There are also prompts in progress for analysis of the videos. Currently the only prompt is for unverifiable or potentially misleading facts. Eventually the goal is to have a fact check pipeline and other pipelines for analyzing other elements of transcripts. 

# Open Issues
- UX for inputting youtube video link and getting information back 
    - UX for processing multiple videos (such as multiple videos from one channel)
    - UX to visualize results from query / video analysis 
- Connect to search tool (similar to stochasticity) for fact checking 
    - Create UX to present identified potentially misleading or false facts and then give option to investigate further
- Develop a fact checking pipeline 
    - Add a reliable way to find relevant facts from transcript
    - Add a way to search for each of the facts
        - Currently thinking of doing transcript->list of facts->formulate search queries->search
        - This is a lot of steps though so I'll try transcripts->formulate search queries, skipping list of facts at some point
    - Display in UX
- Develop some sort of opinionation measure and way to display it
- Add options for inputting own's one prompt 
- Currently whisper and youtube transcript caches are mixed. Ideally they would be separate.
- Add diarization
- Add text streaming for GPT results
- Option to use YouTube transcript if it exists (as opposed to using Whisper)
- Keep an eye on/figure out protobuf version conflict (grpcio-tools and google-api-core vs streamlit)

## Stretch Goals
- Add channel analysis 
- Add graph-based visualization (ex: comparisons on factors such as opinions per minute, political lean, misleading facts per 1000 words)
- Host website 
- Basic visualization around custom prompts 
- Add support for longer videos, maybe by breaking up the video

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