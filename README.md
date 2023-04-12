# Overview 
The purpose of this repository is a pipeline for YouTube video analysis and specifically fact-check. Videos can have transcripts retrieved or generated using Whisper with a flag. There are also prompts in progress for analysis of the videos. Currently the only prompt is for unverifiable or potentially misleading facts. Eventually the goal is to have a fact check pipeline and other pipelines for analyzing other elements of transcripts. 

# Open Issues
- Add support for downloading youtube video audio automatically
- UX for inputting youtube video link and getting information back 
    - UX for processing multiple videos (such as multiple videos from one channel)
    - UX to visualize results from query / video analysis 
- Connect to search tool (similar to stochasticity) for fact checking 
    - Create UX to present identified potentially misleading or false facts and then give option to investigate further
- Caching for transcript retrieval and for video MP3
- Option to prefer manually created YouTube transcript or using Whisper
- Limit to reject videos over a certain length (likely around 15 minutes)
    - Eventually add support for longer videos, potentially by breaking up the video
- Add options for inputting own's one prompt 


## Stretch Goals
- Add channel analysis 
- Add graph-based visualization (ex: comparisons on factors such as opinions per minute, political lean, misleading facts per 1000 words)
- Host website 
- Basic visualization around custom prompts 