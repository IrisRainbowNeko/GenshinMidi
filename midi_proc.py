import mido
from mido import Message, MidiFile, MidiTrack
import numpy as np
from collections import Counter
import argparse

def tracks_mix(mid, tracks):
    note_list=[]
    time_sum = 0
    note_on_dict={}
    tempo=500000
    print(len(tracks))

    for track in tracks:
        time_sum = 0
        for msg in track:#每个音轨的消息遍历
            if msg.type=='set_tempo':
                tempo=msg.tempo
                print('ticks_per_beat', mid.ticks_per_beat)
                print(msg, mido.tick2second(msg.time, mid.ticks_per_beat, tempo))
            time_sum+=mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
            if msg.type=='note_on':
                note_on_dict[msg.note]=time_sum
            elif msg.type=='note_off':
                note_list.append([note_on_dict[msg.note], time_sum, msg.note])

    note_list.sort(key=lambda x:x[0])
    note_list=np.array(note_list)

    return note_list

def note_overleap_mix(note_list, iou_th=0.2):
    #合并有重叠的音符
    rm_idxs=[]
    for i, note in enumerate(note_list):
        if i in rm_idxs:
            continue
        u=i+1
        while u<len(note_list) and note_list[u][0]<note[1]:
            note_next=note_list[u]
            if note[2] == note_next[2]:
                if note_next[1]<note[1]:
                    rm_idxs.append(u)
                len_u = note_next[1]-note_next[0]
                len_i = note[1]-note[0]
                if (note_next[1]-note[0])/min(len_i, len_u)>iou_th:
                    if len_i<len_u:
                        rm_idxs.append(i)
                        break
                    else:
                        rm_idxs.append(u)
            u+=1
    print('overleap:', len(rm_idxs))
    note_list=np.delete(note_list, rm_idxs, axis=0)
    return note_list

def note_short_rm(note_list, time_th=0.05):
    #合并有重叠的音符
    rm_idxs=[]
    for i, note in enumerate(note_list):
        if note[1]-note[0] < time_th:
            rm_idxs.append(i)
    print('short:', len(rm_idxs))
    note_list=np.delete(note_list, rm_idxs, axis=0)
    return note_list

def make_midi(note_list, path):
    mid = MidiFile(ticks_per_beat=220)  # 给自己的文件定的.mid后缀
    track = MidiTrack()  # 定义声部，一个MidoTrack()就是一个声部
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(Message('program_change', channel=0, program=2, time=0))

    msg_list=[]
    for note in note_list:
        msg_list.append((note[0], 'note_on', note[2]))
        msg_list.append((note[1], 'note_off', note[2]))
    msg_list.sort(key=lambda x: x[0])

    last_time=0
    for msg in msg_list:
        dt=mido.second2tick(msg[0]-last_time, mid.ticks_per_beat, 500000)
        track.append(Message(msg[1], note=int(msg[2]), velocity=64, time=int(dt), channel=0))
        last_time=msg[0]
    mid.tracks.append(track)
    mid.save(path)

def note_mix(note_list, iou_th=0.7):
    #合并同时间音符，适应谱子
    note_list_mix=[]
    rm_idxs = []
    for i, note in enumerate(note_list):
        if i in rm_idxs:
            continue
        u = i + 1
        n_start=note[0]
        n_end=note[1]
        note_v_list=[note[2]]
        while u < len(note_list) and note_list[u][0] < note[1]:
            note_next = note_list[u]
            uni_l = min(note[0], note_next[0])
            uni_h = max(note[1], note_next[1])
            in_l = max(note[0], note_next[0])
            in_h = min(note[1], note_next[1])
            if (in_h-in_l)/(uni_h-uni_l) > iou_th:
                rm_idxs.append(u)
                n_start=min(n_start, uni_l)
                n_end=max(n_end, uni_h)
                note_v_list.append(note_next[2])
            u += 1
        note_v_list=np.array(note_v_list)
        note_list_mix.append([n_start, n_end, round(np.mean(note_v_list)), len(note_v_list)])
    print('mix:', len(rm_idxs))
    return note_list_mix

def note2script(note_list, time_th=0.03, note_cap=6, beat=69):
    #求有相交的子集
    note_group_list=[]
    i=0
    while i<len(note_list):
        note=note_list[i]
        note_group=[note]
        i = i + 1
        max_end=note[1]
        while i < len(note_list) and note_list[i][0] < max_end-time_th:
            note_next = note_list[i]
            note_group.append(note_next)
            max_end=max(max_end, note_next[1])
            i+=1
        note_group_list.append(note_group)
    print('note count:', len(note_list))
    print('group count:', len(note_group_list))
    result=[]
    for note_group in note_group_list:
        note_group=np.array(note_group)
        note_group_agg=dict(Counter(note_group[:,2]))

        note_set=list(note_group_agg.keys())
        note_set.sort()
        click=np.array(note_set)
        click_note_map={int(k):int(v) for k,v in zip(note_set, click)}

        for i in range(note_group.shape[0]):
            note_group[i,2]=click_note_map[int(note_group[i,2])]%note_cap

        result.append(note_group)

    result=np.vstack(result)
    result[:,:2]=(result[:,:2]*1000)/beat
    result=result.astype(int)
    result=result[np.argsort(result[:,0]),:]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OF Generate')
    parser.add_argument('-p', '--path', default='midi/xg.midi', type=str)
    args = parser.parse_args()

    mid = mido.MidiFile(args.path, clip=True)
    note_list = tracks_mix(mid, mid.tracks)
    note_list = note_overleap_mix(note_list)
    note_list = note_short_rm(note_list)

    #make_midi(note_list, 'test.mid')

    note_list = note_mix(note_list)
    script=note2script(note_list)
    np.save(f'{args.path[:-4]}npy', script)
