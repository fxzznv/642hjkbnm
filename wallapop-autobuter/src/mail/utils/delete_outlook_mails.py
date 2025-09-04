import json
import time
from datetime import datetime, timezone

import jwt
from jwt import PyJWTError
from urllib.parse import quote

import requests

from src.mail.mail_api import generate_guid

def extract_rule_id(raw_identity):
    return raw_identity.split('\\')[-1]

def extract_puid_tenatid(id_token):
    try:
        # Декодируем токен без проверки подписи (verify=False, т.к. у нас нет ключей)
        decoded = jwt.decode(id_token, options={"verify_signature": False}, algorithms=["RS256"])

        # Извлекаем puid и tid
        puid = decoded.get("puid")
        tid = decoded.get("tid")

        if not puid or not tid:
            return None

        print(f"puid : {puid}")
              # f"tenat_id: {tid}")

        return puid, tid

    except PyJWTError as e:
        print(f"Ошибка декодирования JWT: {e}")
        return None

def get_outlook_folders(session, auth_token, puid):
    url = "https://outlook.live.com/owa/0/service.svc?action=GetOwaUserConfiguration&app=Mail&n=13"

    headers = {
        "action": "GetOwaUserConfiguration",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        "ms-cv": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "referer": "",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-owa-urlpostdata": "%7B%7D",  # URL-encoded "{}"
        "x-req-source": "Mail"
    }
    try:
        response = session.post(url, headers=headers)

        data = response.json()

        inbox_folder_id = data['SessionSettings']['DefaultFolderIds'][5]['Id']
        deleted_folder_id = data['SessionSettings']['DefaultFolderIds'][3]['Id']

        print(response.status_code)
        print(f"Inbox Folder ID: {inbox_folder_id}\nDeleted Folder ID: {deleted_folder_id}")
        return inbox_folder_id, deleted_folder_id

    except Exception as e:
        print(f"Exception: {response.status_code}, {response.text}: {e}")

def create_inbox_rule(session, auth_token, deleted_folderid, puid, rule_name="xzc"):
    url = "https://outlook.live.com/owa/0/service.svc?action=NewInboxRule&app=Mail&n=57"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "action": "NewInboxRule",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        "ms-cv": generate_guid(),
        "origin": "https://outlook.live.com",
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        # "x-owa-urlpostdata":
        "x-req-source": "Mail",
        "x-tenantid": "84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    }
    payload = {
        "__type": "NewInboxRuleRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "InboxRule": {
            "Name": rule_name,
            "FromAddressContainsWords": ["info@info.wallapop.com"],
            "MoveToFolder": {
                "DisplayName": "Удалённые",
                "RawIdentity": deleted_folderid
            },
            "StopProcessingRules": True
        }
    }
    try:
        response = session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"create rule: {response.status_code}: {response.json()}")
        return response
    except Exception as e:
        print(f"Exception: {response.status_code},{response.text}. {e}")

def get_inbox_rule_id(session, auth_token, puid):
    url = "https://outlook.live.com/owa/0/service.svc?action=GetInboxRule&app=Mail&n=27"

    request_body = {
        "__type": "GetInboxRuleRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "UseServerRulesLoader": True
    }

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "action": "GetInboxRule",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        "ms-cv": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-owa-urlpostdata": json.dumps(request_body),
        "x-req-source": "Mail",
        "x-tenantid": "84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    }

    try:
        response = session.post(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            # print("Полный ответ получен:")
            # print(json.dumps(data, indent=2, ensure_ascii=False))

            if data.get('InboxRuleCollection', {}).get('InboxRules'):
                first_rule = data['InboxRuleCollection']['InboxRules'][0]
                raw_identity = first_rule.get('Identity', {}).get('RawIdentity')
                if raw_identity:
                    print(f"RawIdentity: {raw_identity}")
                    formatted_rule_id = extract_rule_id(raw_identity)
                    return raw_identity, formatted_rule_id
                else:
                    print("RawIdentity не найден в ответе")
            else:
                print("Нет правил в ответе")
        else:
            print(f"Ошибка: {response.status_code}, Response: {response.text}")
        return None

    except Exception as e:
        print(f"Exception: {response.status_code}, {response.text}: {e}")
        return None

def execute_inbox_rule(session, auth_token, inbox_folderid, rule_id, formatted_rule_id, puid, rule_name="xzc"):
    request_body = {
        "__type": "ExecuteInboxRulesJsonRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "Body": {
            "__type": "ExecuteInboxRulesRequest:#Exchange",
            "InboxRuleIds": [rule_id],
            "SourceFolderId": {
                "__type": "FolderId:#Exchange",
                "Id": inbox_folderid
            },
            "BulkActionRequest": True,
            "BulkActionCustomData": json.dumps({
                "Scenario": "RunRuleNow",
                "ruleName": rule_name,
                "ruleId": formatted_rule_id
            })
        }
    }

    json_payload = json.dumps(request_body)
    encoded_payload = quote(json_payload)

    headers = {
        "authority": "outlook.live.com",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,be;q=0.6,tg;q=0.5",
        "action": "ExecuteInboxRules",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        # "cookie": cookie,
        "ms-cv": generate_guid(),
        "origin": "https://outlook.live.com",
        "prefer": "IdType=\"ImmutableId\", exchange.behavior=\"IncludeThirdPartyOnlineMeetingProviders\"",
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-owa-urlpostdata": encoded_payload,
        "x-req-source": "Mail",
        "x-tenantid": "84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    }

    url = "https://outlook.live.com/owa/0/service.svc?action=ExecuteInboxRules&app=Mail&n=67"

    try:
        response = session.post(url, headers=headers, data="")
        response.raise_for_status()
        print(f"execute rule: {response.status_code}, {response.json()}")
        return response
    except Exception as e:
        print(f"Exception: {response.status_code},{response.text}. {e}")

def disable_inbox_rule(session, auth_token, raw_identity, puid):
    url = 'https://outlook.live.com/owa/0/service.svc?action=DisableInboxRule&app=Mail&n=137'

    payload = {
        "__type": "DisableInboxRuleRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "Identity": {
            "DisplayName": raw_identity,
            "RawIdentity": raw_identity
        }
    }

    json_payload = json.dumps(payload)
    encoded_payload = quote(json_payload)

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'action': 'DisableInboxRule',
        'authorization': f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        'content-length': '0',
        'content-type': 'application/json; charset=utf-8',
        'ms-cv': generate_guid(),
        'origin': 'https://outlook.live.com',
        'prefer': 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        'priority': 'u=1, i',
        'referer': 'https://outlook.live.com/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-anchormailbox': f'PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa',
        'x-owa-correlationid': generate_guid(),
        'x-owa-hosted-ux': 'false',
        'x-owa-sessionid': generate_guid(),
        'x-owa-urlpostdata': encoded_payload,
        'x-req-source': 'Mail',
        'x-tenantid': '84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa'
    }

    try:
        response = session.post(url, headers=headers, data="")
        response.raise_for_status()
        print(f"delete rule {response.status_code}, {response.json()}")
        return response
    except Exception as e:
        print(f"Exception: {response.status_code},{response.text}. {e}")

def delete_inbox_rule(session, auth_token, rule_id, puid):
    payload = {
        "__type": "RemoveInboxRuleRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "Identity": {
            "DisplayName": rule_id,
            "RawIdentity": rule_id
        }
    }

    json_payload = json.dumps(payload)
    encoded_payload = quote(json_payload)

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,be;q=0.6,tg;q=0.5",
        "action": "RemoveInboxRule",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        # "cookie": cookie,
        "ms-cv": generate_guid(),
        "origin": "https://outlook.live.com",
        "prefer": "IdType=\"ImmutableId\", exchange.behavior=\"IncludeThirdPartyOnlineMeetingProviders\"",
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-owa-urlpostdata": encoded_payload,
        "x-req-source": "Mail",
        "x-tenantid": "84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    }

    url = "https://outlook.live.com/owa/0/service.svc?action=RemoveInboxRule&UA=0&app=Mail&n=85"

    try:
        response = session.post(url, headers=headers, data="")
        response.raise_for_status()
        print(f"delete rule {response.status_code}, {response.json()}")
        return response
    except Exception as e:
        print(f"Exception: {response.status_code},{response.text}. {e}")

def empty_deleted_folder(session, auth_token, deleted_folderid, puid):
    payload = {
        "__type": "EmptyFolderJsonRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "Body": {
            "__type": "EmptyFolderRequest:#Exchange",
            "FolderIds": [{
                "__type": "FolderId:#Exchange",
                "Id": deleted_folderid
            }],
            "AllowSearchFolder": True,
            "DeleteType": "HardDelete",
            "DeleteSubFolders": False,
            "SuppressReadReceipt": True,
            "ItemIdsToExclude": [],
            "BulkActionRequest": True,
            "BulkActionBatchSize": 200
        }
    }

    json_payload = json.dumps(payload)
    encoded_payload = quote(json_payload)

    headers = {
        "action": "EmptyFolder",
        "authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        # "cookie": cookie,
        "ms-cv": generate_guid(),
        "prefer": "IdType=\"ImmutableId\", exchange.behavior=\"IncludeThirdPartyOnlineMeetingProviders\"",
        "referer": "https://outlook.live.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-owa-urlpostdata": encoded_payload,
        "x-req-source": "Mail"
    }

    url = "https://outlook.live.com/owa/0/service.svc?action=EmptyFolder&UA=0&app=Mail&n=147"

    try:
        response = session.post(url, headers=headers, data="")
        response.raise_for_status()
        print(f"empty del folder {response.status_code}, {response.json()}")
        return response
    except Exception as e:
        print(f"Exception: {response.status_code},{response.text}. {e}")

def delete_message_by_token(session, auth_token, inbox_folderid, puid, mail_token):
    url = "https://outlook.live.com/owa/0/service.svc?action=ApplyConversationAction&app=Mail&n=52"

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    current_timestamp = now_utc.replace('+00:00', '.000Z')

    payload = {
            "__type": "ApplyConversationActionJsonRequest:#Exchange",
            "Header": {
                "__type": "JsonRequestHeaders:#Exchange",
                "RequestServerVersion": "V2018_01_08",
                "TimeZoneContext": {
                    "__type": "TimeZoneContext:#Exchange",
                    "TimeZoneDefinition": {
                        "__type": "TimeZoneDefinitionType:#Exchange",
                        "Id": "Greenwich Standard Time"
                    }
                }
            },
            "Body": {
                "__type": "ApplyConversationActionRequest:#Exchange",
                "ConversationActions": [
                    {
                        "__type": "ConversationAction:#Exchange",
                        "Action": "SetReadState",
                        "ConversationId": {
                            "__type": "ItemId:#Exchange",
                            "Id": mail_token
                        },
                        "IsRead": True,
                        "ConversationLastSyncTime": f"{current_timestamp}",
                        "SuppressReadReceipts": True,
                        "ContextFolderId": {
                            "__type": "TargetFolderId:#Exchange",
                            "BaseFolderId": {
                                "__type": "FolderId:#Exchange",
                                "Id": inbox_folderid
                            }
                        }
                    }
                ],
                "ReturnMovedItemIds": False
            }
        }

    json_payload = json.dumps(payload)
    encoded_payload = quote(json_payload)

    headers = {
        "x-req-source": "Mail",
        "Authorization": f'MSAuth1.0 usertoken="{auth_token}", type="MSACT"',
        "Action": "ApplyConversationAction",
        "Referer": "",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-hosted-ux": "false",
        "ms-cv": generate_guid(),
        "x-owa-sessionid": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "x-owa-actionsource": "ApplyConversationAction_SetReadState",
        "x-owa-urlpostdata": encoded_payload,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Content-Type": "application/json; charset=utf-8",
        "x-owa-correlationid": generate_guid()
    }

    response = requests.post(url, headers=headers, data="")
    print(f"{response.status_code},{response.text}")

    url = "https://outlook.live.com/owa/0/service.svc?action=ApplyConversationAction&app=Mail&n=62"

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    current_timestamp = now_utc.replace('+00:00', '.000Z')

    payload = {
        "__type": "ApplyConversationActionJsonRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "UTC"
                }
            }
        },
        "Body": {
            "__type": "ApplyConversationActionRequest:#Exchange",
            "ConversationActions": [
                {
                    "__type": "ConversationAction:#Exchange",
                    "Action": "Delete",
                    "ConversationId": {
                        "__type": "ItemId:#Exchange",
                        "Id": mail_token
                    },
                    "DeleteType": "MoveToDeletedItems",
                    "ConversationLastSyncTime": f"{current_timestamp}",
                    "SuppressReadReceipts": True,
                    "ContextFolderId": {
                        "__type": "TargetFolderId:#Exchange",
                        "BaseFolderId": {
                            "__type": "FolderId:#Exchange",
                            "Id": inbox_folderid
                        }
                    }
                }
            ],
            "ReturnMovedItemIds": False
        }
    }

    json_payload = json.dumps(payload)
    encoded_payload = quote(json_payload)


    headers = {
        "action": "ApplyConversationAction",
        "authorization": f'MSAuth1.0 usertoken={auth_token}, type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        "ms-cv": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "referer": "",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-actionsource": "ApplyConversationAction_Delete",
        "x-owa-correlationid": generate_guid(),
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-req-source": "Mail",
        "x-owa-urlpostdata": encoded_payload
    }

    try:
        response = session.post(url, headers=headers, data="")

        # First check if response has content
        if not response.text:
            print(f"Empty response from server. Status code: {response.status_code}")
            return

        try:
            json_response = response.json()
            print("Удаление сообщений по токену: ", response.status_code, json_response)
        except ValueError:
            print(f"Invalid JSON response. Status code: {response.status_code}, Response text: {response.text}")

    except Exception as e:
        print(f"Error in delete_message_by_token: {str(e)}")

def make_inbox_rule(session,auth_token,deleted_folderid,inbox_folderid,puid):
    try:
        create_inbox_rule(session, auth_token, deleted_folderid, puid)
        rule_id, formatted_rule_id = get_inbox_rule_id(session, auth_token, puid)
        return rule_id, formatted_rule_id
    except Exception as e:
        print(f"Make and execute inbox rule, Exception: {e}")

def delete_messages_by_exiting(session,auth_token,inbox_folderid, deleted_folderid,rule_id, formatted_rule_id, puid):
    try:
        execute_inbox_rule(session, auth_token, inbox_folderid, rule_id, formatted_rule_id, puid)
        empty_deleted_folder(session, auth_token,deleted_folderid, puid)
    except Exception as e:
        print(f"delete messages by exiting, Exception: {e}")

def delete_all_walla_messages(session, auth_token, puid, rule_name="zxczxc"):
    try:
        inbox_folderid, deleted_folderid = get_outlook_folders(session, auth_token, puid)
        create_inbox_rule(session, auth_token, deleted_folderid, puid)
        rule_id, formatted_rule_id = get_inbox_rule_id(session, auth_token, puid)
        execute_inbox_rule(session, auth_token, inbox_folderid, rule_id, formatted_rule_id, puid)
        time.sleep(2)
        disable_inbox_rule(session,auth_token,rule_id,puid)
        delete_inbox_rule(session, auth_token, rule_id, puid)
        delete_inbox_rule(session, auth_token, rule_id, puid)
        empty_deleted_folder(session, auth_token,deleted_folderid, puid)

        # delete_message_by_token(session, auth_token,deleted_folderid,puid,
        #                         mail_token="AQQkADAwATZiZmYAZC02NGNjAC02ZjMwLTAwAi0wMAoAEAA9dGuRAr0UTKPeCbu4UBp5")

        print('Все письма от валлапопа удалены')
    except Exception as e:
        print(f"Delete all walla messages block Exception: {e}")

if __name__ == "__main__":
    session = requests.Session()
    auth_token = ""
    inbox_folderid = "AQMkADAwATYwMAItNjFkYy1kNjBmLTAwAi0wMAoALgAAAziy7bwSGdZGpzG3It1JTRwBAHjf1Zl7metKg4q5mIZhsxgAAAIBDAAAAA=="
    deleted_folderid = ""
    create_inbox_rule(session, auth_token, inbox_folderid)
    # extract_puid_tenatid(id_token=None)
    # get_oulook_folders(session, )
