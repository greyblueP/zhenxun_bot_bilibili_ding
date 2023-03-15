import json
from pathlib import Path

file = Path.cwd()/'my_plugins'/'bilibili_ding'
# {
#     'mid': {
#         'info': [
#             # 昵称 Name
#             # 直播间是否存在 RoomStatus
#             # 是否开播 LiveStatus
#             # 动态时间 LatestDynamicTime
#         ],
#         'group': [
#             True,  # 是否推送动态
#             True,  # 是否推送直播
#             False,  # 是否推送下播
#             False,  # 是否@全体
#             False,  # 是否@单体
#             [
#                 # QQ号
#             ]
#         ]
#     }
# }


def WriteList(data):  # 写入文件
    with open(f'{file}/list.json', 'w', encoding='utf-8')as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def ReadList():  # 读取文件
    try:
        with open(f'{file}/list.json', 'r', encoding='utf-8')as f:
            data = json.load(f)
            return data
    except:
        WriteList({})
        return {}


def ReadDynamicMid():  # 读取动态mid
    data = ReadList()
    FollowList = []
    for mid in data:
        FollowList.append(mid)
    return FollowList


def ReadLiveMid():  # 读取直播推送mid
    data = ReadList()
    FollowList = []
    for mid in data:
        for group in data[mid]:
            if group != 'info' and data[mid][group][1] == True:
                FollowList.append(mid)
                break
    return FollowList


def CreateMid(mid: str, group: str, Name: str, LiveRoom: str):  # 加入新mid
    data = ReadList()
    if mid not in data:
        data[mid] = {
            'info': [Name, LiveRoom, 0, 0],
            group: [True, True, True, False, False, []]
        }
        WriteList(data)
        return True
    if group not in data[mid]:
        data[mid][group] = [True, True, True, False, False, []]
        WriteList(data)
        return True
    else:
        return "UP已存在于列表"


def DeleteMid(mid: str, group: str):  # 删除mid
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            del data[mid][group]
            if len(data[mid]) == 1:
                del data[mid]
            WriteList(data)
            return True
        else:
            return "UP不存在于列表,请检查UID是否错误"
    else:
        return "UP不存在于列表,请检查UID是否错误"


def ReadName(mid: str):  # 读取昵称
    data = ReadList()
    Name = data[mid]['info'][0]
    return Name


def ReadRoom(mid: str):  # 读取直播存在情况及开播状态
    data = ReadList()
    LiveRoom = data[mid]['info'][1]
    LiveStatus = data[mid]['info'][2]
    return LiveRoom, LiveStatus


def ReadDynamicTime(mid: str):  # 读取动态时间
    data = ReadList()
    DynamicTime = data[mid]['info'][3]
    return DynamicTime


def ResetLiveStatus(mid: str, LiveStatus: int):  # 重置开播状态
    data = ReadList()
    data[mid]['info'][2] = LiveStatus
    WriteList(data)
    return True


def ResetDynamicTime(mid: str, DynamicTime: int):  # 重置动态时间
    data = ReadList()
    data[mid]['info'][3] = DynamicTime
    WriteList(data)
    return True


def ReadGroup(mid: str):  # 读取群列表
    data = ReadList()
    GroupList = data[mid]
    del GroupList['info']
    return GroupList


def ReadGroupList(group: str):  # 读取群关注列表
    data = ReadList()
    FollowList = {}
    for mid in data:
        if group in data[mid]:
            FollowList[mid] = data[mid][group]
    return FollowList


def ReadGroupQQ(group: str, mid: str):  # 读取群qq列表
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            QQList = data[mid][group][5]
            return QQList
        else:
            return False


def OnOption(mid: str, group: str, num: int):  # 开启功能
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            data[mid][group][num] = True
            WriteList(data)
            return True
        else:
            return "UP不存在于列表,请检查UID是否错误"
    else:
        return "UP不存在于列表,请检查UID是否错误"


def OffOption(mid: str, group: str, num: int):  # 关闭功能
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            data[mid][group][num] = False
            WriteList(data)
            return True
        else:
            return "UP不存在于列表,请检查UID是否错误"
    else:
        return "UP不存在于列表,请检查UID是否错误"


def AddAtSome(mid: str, group: str, qq: str):  # 添加qq
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            if qq not in data[mid][group][5]:
                data[mid][group][5].append(qq)
                WriteList(data)
                return True
            else:
                return 1
        else:
            return 2
    else:
        return 2


def DelAtSome(mid: str, group: str, qq: str):  # 删除qq
    data = ReadList()
    if mid in data:
        if group in data[mid]:
            if qq in data[mid][group][5]:
                data[mid][group][5].remove(qq)
                WriteList(data)
                return True
            else:
                return 1
        else:
            return 2
    else:
        return 2
