import re

import nonebot
from nonebot import on_command, require
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import (Bot, GroupMessageEvent, Message)
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.permission import (GROUP, GROUP_ADMIN,
                                                    GROUP_OWNER,
                                                    PRIVATE_FRIEND)
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from . import data_source, model


__zx_plugin_name__ = "哔哩哔哩订阅"
__plugin_usage__ = """
usage：
    大D特D！
    指令：
        关注 UID
        取关 UID
        *列表
        开启动态 UID
        关闭动态 UID
        开启直播 UID
        关闭直播 UID
        开启下播 UID
        关闭下播 UID
        开启全体 UID
        关闭全体 UID
        开启单体 UID
        关闭单体 UID
        *开播叫我 UID
        *不要叫我 UID
        *单体列表 UID
        \n(请将UID替换为需操作的B站UID)
""".strip()
__plugin_des__ = "b站推送"
__plugin_cmd__ = [
    "关注/取关/列表/开启动态/关闭动态/开启直播/关闭直播/开启下播/关闭下播/开启全体/关闭全体/开启单体/关闭单体/开播叫我/不要叫我/单体列表",
]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 0.1
__plugin_author__ = "greyblueP"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": [
        "关注",
        "取关",
        "列表",
        "开启动态",
        "关闭动态",
        "开启直播",
        "关闭直播",
        "开启下播",
        "关闭下播",
        "开启全体",
        "关闭全体",
        "开启单体",
        "关闭单体",
        "开播叫我",
        "不要叫我",
        "单体列表",
    ],
}

addup = on_command('关注', rule=to_me(), priority=5,
                   permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
removeup = on_command('取关', rule=to_me(), priority=5,
                      permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
alllist = on_command('列表', rule=to_me(), priority=5, permission=GROUP, )
ondynamic = on_command('开启动态', rule=to_me(), priority=5,
                       permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
offdynamic = on_command('关闭动态', rule=to_me(), priority=5,
                        permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
onlive = on_command('开启直播', rule=to_me(), priority=5,
                    permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
offlive = on_command('关闭直播', rule=to_me(), priority=5,
                     permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
onliveend = on_command('开启下播', rule=to_me(), priority=5,
                       permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
offliveend = on_command('关闭下播', rule=to_me(), priority=5,
                        permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
onatall = on_command('开启全体', rule=to_me(), priority=5,
                     permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
offatall = on_command('关闭全体', rule=to_me(), priority=5,
                      permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
onatsingle = on_command('开启单体', rule=to_me(), priority=5,
                        permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
offatsingle = on_command('关闭单体', rule=to_me(), priority=5,
                         permission=GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND | SUPERUSER, )
onatme = on_command('开播叫我', rule=to_me(), priority=5, permission=GROUP, )
offatme = on_command('不要叫我', rule=to_me(), priority=5, permission=GROUP, )
singlelist = on_command('单体列表', rule=to_me(), priority=5, permission=GROUP, )

scheduler = require('nonebot_plugin_apscheduler').scheduler

live_index = 0
dynamic_index = 0


@scheduler.scheduled_job('interval', seconds=20, id='bilibili_live')
async def live():  # 定时推送直播间状态
    (schedBot,) = nonebot.get_bots().values()
    # 确认查询的是哪个主播
    global live_index
    mids = model.ReadLiveMid()
    if mids == []:
        return
    if live_index >= len(mids):
        live_index = 0
    mid = mids[live_index]
    # 获取主播信息
    RoomStatus, LiveStatus = model.ReadRoom(mid)
    if RoomStatus != 1:
        return
    Name = model.ReadName(mid)
    status, live_status, content = await data_source.LiveRoomInfo(mid)
    if status != 0:
        logger.error(f'{Name}直播状态更新失败')
        return
    if LiveStatus == live_status:
        live_index += 1
        return
    logger.info(f'检测到 {Name} 直播状态更新')
    model.ResetLiveStatus(mid, live_status)
    Groups = model.ReadGroup(mid)
    for group in Groups:
        try:
            if Groups[group][1] == True:  # 允许推送直播
                if live_status != 0:
                    if Groups[group][3] == True:  # @全体成员
                        await schedBot.call_api('send_msg', **{
                            'message': MessageSegment.at('all'),
                            'group_id': group
                        })
                    if Groups[group][4] == True:  # @单体成员
                        txt = ''
                        for qq in Groups[group][5]:
                            txt += MessageSegment.at(qq)+'\n'
                        txt = txt[:-1]
                        await schedBot.call_api('send_msg', **{
                            'message': txt,
                            'group_id': group
                        })
                    await schedBot.call_api('send_msg', **{
                        'message': content,
                        'group_id': group
                    })
                if live_status == 0 and Groups[group][2] == True:  # 允许推送下播
                    await schedBot.call_api('send_msg', **{
                        'message': content,
                        'group_id': group
                    })
        except Exception as e:
            logger.error(f'直播间状态推送出错：{e}')
    live_index += 1


@scheduler.scheduled_job('interval', seconds=20, id='bilibili_dynamic')
async def dynamic():  # 定时推送最新用户动态
    (schedBot,) = nonebot.get_bots().values()
    # 确认查询的是哪个UP
    global dynamic_index
    mids = model.ReadDynamicMid()
    if mids == []:
        return
    if dynamic_index >= len(mids):
        dynamic_index = 0
    mid = mids[live_index]
    # 获取UP信息
    LastDynamicTime = model.ReadDynamicTime(mid)
    Name = model.ReadName(mid)
    status, NewDynamicTime, content = await data_source.LatestDynamicInfo(mid, LastDynamicTime)
    if status != 0:
        logger.error(f'{Name}动态查询失败')
        return
    if NewDynamicTime == '':
        dynamic_index += 1
        return
    if content == '':
        model.ResetDynamicTime(mid, NewDynamicTime)
    logger.info(f'检测到 {Name} 动态更新')
    model.ResetDynamicTime(mid, NewDynamicTime)
    Groups = model.ReadGroup(mid)
    for group in Groups:
        try:
            if Groups[group][0] == True:
                await schedBot.call_api('send_msg', **{
                    'message': content,
                    'group_id': group
                })
        except Exception as e:
            logger.error(f'用户动态推送出错：{e}')
    dynamic_index += 1


@addup.handle()  # 添加关注
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关注 UID'
    is_group = int(isinstance(event, GroupMessageEvent))
    if is_group != 1:
        msg = '请在群聊中进行关注操作!'
    else:
        if mid != '':
            # 获取群号
            group = event.get_session_id()
            if not group.isdigit():
                group = group.split('_')[1]
            status, Name, RoomStatus = await data_source.GetInfo(mid)
            Back = model.CreateMid(mid, group, Name, RoomStatus)
            if Back == True:
                msg = f'已成功关注{Name}({mid})!'
            else:
                msg = Back
    Msg = Message(msg)
    await alllist.finish(Msg)


@removeup.handle()  # 取消关注
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：取消关注 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Name = model.ReadName(mid)
        Back = model.DeleteMid(mid, group)
        if Back == True:
            msg = f'已成功取关{Name}({mid})!'
        else:
            msg = Back
    Msg = Message(msg)
    await alllist.finish(Msg)


@alllist.handle()  # 查看群关注列表
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取群号
    group = event.get_session_id()
    if not group.isdigit():
        group = group.split('_')[1]
    Back = model.ReadGroupList(group)
    if Back != {}:
        msg = '本群关注列表：\n'
        for mid in Back:
            Name = model.ReadName(mid)
            msg += f'\n{Name}({mid})\n'
            msg += f'动态:{Back[mid][0]} 直播:{Back[mid][1]} 下播:{Back[mid][2]}\n全体:{Back[mid][3]} 单体:{Back[mid][4]}'
            msg = msg.replace('True', '开').replace('False', '关')
    else:
        msg = '本群未关注任何UP!'
    Msg = Message(msg)
    await alllist.finish(Msg)


@ondynamic.handle()  # 启动动态推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开启动态 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OnOption(mid, group, 0)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开启动态推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await ondynamic.finish(Msg)


@offdynamic.handle()  # 关闭动态推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关闭动态 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OffOption(mid, group, 0)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})关闭动态推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await offdynamic.finish(Msg)


@onlive.handle()  # 启动直播推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开启直播 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OnOption(mid, group, 1)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开启直播推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await onlive.finish(Msg)


@offlive.handle()  # 关闭直播推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关闭直播 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OffOption(mid, group, 1)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})关闭直播推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await offdynamic.finish(Msg)


@onliveend.handle()  # 启动下播推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开启下播 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OnOption(mid, group, 2)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开启下播推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await onliveend.finish(Msg)


@offliveend.handle()  # 关闭下播推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关闭下播 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OffOption(mid, group, 2)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})关闭下播推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await offliveend.finish(Msg)


@onatall.handle()  # 启动全体成员推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开启全体 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OnOption(mid, group, 3)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开启全体成员推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await onatall.finish(Msg)


@offatall.handle()  # 关闭全体成员推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关闭全体 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OffOption(mid, group, 3)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})关闭全体成员推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await offatall.finish(Msg)


@onatsingle.handle()  # 启动单体成员推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开启单体 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OnOption(mid, group, 4)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开启单体成员推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await onatsingle.finish(Msg)


@offatsingle.handle()  # 关闭单体成员推送
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：关闭单体 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.OffOption(mid, group, 4)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})关闭单体成员推送!'
        else:
            msg = Back
    Msg = Message(msg)
    await offatsingle.finish(Msg)


@onatme.handle()  # 开播@我
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：开播叫我 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        # 获取qq号
        qq = event.get_user_id()
        Back = model.AddAtSome(mid, group, qq)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开播时你将会被@!'
        elif Back == 1:
            msg = '你已经在开播@列表中了！'
        else:
            msg = 'UP不存在于列表,请检查UID是否错误'
    Msg = Message(msg)
    await onatme.finish(Msg)


@offatme.handle()  # 关闭开播@我
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：不要叫我 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        # 获取qq号
        qq = event.get_user_id()
        Back = model.DelAtSome(mid, group, qq)
        if Back == True:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})开播时你将不会被@!'
        elif Back == 1:
            msg = '你不在开播@列表中!'
        else:
            msg = 'UP不存在于列表,请检查UID是否错误'
    Msg = Message(msg)
    await offatme.finish(Msg)


@singlelist.handle()  # 单体成员列表
async def handle(bot: Bot, event: MessageEvent, state: T_State):
    # 获取mid
    mid = str(event.get_message()).strip()
    mid = re.sub('\D', '', mid)
    msg = '指令格式错误！请按照：单体列表 UID'
    if mid != '':
        # 获取群号
        group = event.get_session_id()
        if not group.isdigit():
            group = group.split('_')[1]
        Back = model.ReadGroupQQ(group, mid)
        if Back == False:
            msg = 'UP不存在于列表,请检查UID是否错误'
        elif Back == []:
            msg = '直播通知列表为空!'
        else:
            Name = model.ReadName(mid)
            msg = f'{Name}({mid})的直播通知列表:\n'
            for qq in Back:
                user = await bot.get_group_member_info(group_id=group, user_id=qq)
                username = user['card'] or user['nickname']
                msg += f'  {username}({qq})\n'
    Msg = Message(msg)
    await singlelist.finish(Msg)
