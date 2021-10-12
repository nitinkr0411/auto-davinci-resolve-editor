import imp
import ffmpegutils
import timecode as tc
import os

def prepare_edl(edl_chunks):
    f = open("sample.edl", "w")
    f.write("TITLE: Timeline 1\n")
    f.write("FCM: DROP FRAME\n\n")
    for i, chunk in enumerate(edl_chunks):
        iteration = str(i+1) 
        f.write("{}  AX       V     C        {} {} {} {}\n".format(iteration.zfill(3), chunk[1], chunk[2], chunk[3], chunk[4]))
        f.write("COMMENT:* FROM CLIP NAME: {}\n\n".format(chunk[0]))
    f.close()

# Modify the parameters here
file_extension = ".MOV"
frame_rate = 59.94
timeline_name = "sample"

# Init Resolve Scripting API
lib = "C:\\Program Files\\Blackmagic Design\\Davinci Resolve\\fusionscript.dll"
dvr_script = imp.load_dynamic("fusionscript", lib)
resolve = dvr_script.scriptapp("Resolve")

# Init Resolve Project
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
mediaPool = project.GetMediaPool()
folder = mediaPool.GetRootFolder()
clips = folder.GetClipList()
filtered_clips = filter(lambda file: str(file.GetClipProperty()["Clip Name"]).endswith(file_extension), clips)
sorted_clips = sorted(filtered_clips, key=lambda d: d.GetClipProperty()['Clip Name']) 

recorder_timecode_position = tc.Timecode(frame_rate, "01:00:00:00")
edl_list = []

for clip in sorted_clips:
    chunk_times = ffmpegutils.get_chunk_times(clip.GetClipProperty()['Clip Name'], -30, 0.6, None, None)

    for chunk in chunk_times:
        if chunk[1] - chunk[0] > 1:
            print("================================================================")
            source_time_code_start = tc.Timecode(frame_rate, clip.GetClipProperty()['Start TC'])
            source_time_code_end = tc.Timecode(frame_rate, clip.GetClipProperty()['End TC'])

            in_frame_count = chunk[0] * frame_rate
            out_frame_count = chunk[1] * frame_rate

            clip_time_code_start = source_time_code_start + tc.Timecode(frame_rate, ffmpegutils.frames_to_timecode(in_frame_count, frame_rate, False))
            clip_time_code_stop  = source_time_code_start + tc.Timecode(frame_rate, ffmpegutils.frames_to_timecode(out_frame_count, frame_rate, False))

            # Calculate recorder position
            recorder_time_code_start = str(recorder_timecode_position)
            recorder_time_code_end = recorder_timecode_position + (clip_time_code_stop - clip_time_code_start)
            recorder_timecode_position = recorder_time_code_end

            print("Clip--------------------> " + clip.GetClipProperty()['Clip Name'])
            print("Gap---------------------> " + str(chunk[1] - chunk[0]))
            print("Start in seconds ------->" + str(chunk[0]))
            print("End in seconds --------->" + str(chunk[1]))
            print("Source timecode start---> " + str(source_time_code_start))
            print("Source timecode end-----> " + str(source_time_code_end))
            print("Source timecode in------> " + str(clip_time_code_start))
            print("Source timecode out-----> " + str(clip_time_code_stop))
            print("Recorder timecode in----> " + str(recorder_time_code_start)) 
            print("Recorder timecode out---> " + str(recorder_time_code_end))

            # Append clip to EDL list of cuts
            edl_list.append(
                [clip.GetClipProperty()['Clip Name'], str(clip_time_code_start), str(clip_time_code_stop), str(recorder_time_code_start), str(recorder_time_code_end)]
            )

# export the timeline
prepare_edl(edl_list)

# Bring the saved EDL back to Davinci Resolve
mediaPool.ImportTimelineFromFile(os.getcwd() + "\\"+ timeline_name+ ".edl")




