import configparser
import os
import shutil
import subprocess
import filecmp
import re
import tempfile
import zipfile
import struct
import fnmatch
import sys
import time
import datetime
import threading
import concurrent.futures

try:
    from git import Repo, Actor
except ModuleNotFoundError as e:
    print('Error: GitPython library required (install with "pip install gitpython")')
    quit(-1)

# -------------------------------------------------------------------------------------------------
python_version = sys.version.split(' ', 1)[0]
if python_version < '3.10':
    print(f'Error: Version of python interpreter should start from 3.10 ({python_version})')
    quit(-1)

THREAD_NAME_PREFIX='th'
EXECUTOR = concurrent.futures.ThreadPoolExecutor(thread_name_prefix=THREAD_NAME_PREFIX) #max_workers=4, 
LOCK = threading.RLock()
CONDITION = threading.Condition()

INSTANCE_BANK = "BANK"
INSTANCE_IC = "IC"
INSTANCE_CLIENT = "CLIENT"
INSTANCE_CLIENT_MBA = "CLIENT_MBA"
DIR_TEMP = os.path.join(os.path.abspath(''), '_TEMP')
DIR_BUILD_BK = os.path.join(DIR_TEMP, '_BUILD', 'BK')
DIR_BUILD_IC = os.path.join(DIR_TEMP, '_BUILD', 'IC')
DIR_BEFORE = os.path.join(DIR_TEMP, '_BEFORE')
DIR_AFTER = os.path.join(DIR_TEMP, '_AFTER')
DIR_AFTER_BLS = os.path.join(DIR_AFTER, 'BLS')
DIR_COMPARED = os.path.join(DIR_TEMP, '_COMPARE_RESULT')
DIR_COMPARED_BLS = os.path.join(DIR_COMPARED, 'BLS')
DIR_COMPARED_BLS_SOURCE = os.path.join(DIR_COMPARED_BLS, 'SOURCE')
DIR_COMPARED_BLS_SOURCE_RCK = os.path.join(DIR_COMPARED_BLS_SOURCE, 'RCK')
DIR_COMPARED_CommonLibraries = os.path.join(DIR_COMPARED, 'SETUP', 'CommonLibraries')
DIR_COMPARED_WWW = os.path.join(DIR_COMPARED, 'WWW')
DIR_COMPARED_WWW_react = os.path.join(DIR_COMPARED, 'WWW_react')
DIR_COMPARED_WWW_BSI_SITES = os.path.join(DIR_COMPARED_WWW, 'BSI_SITES')
DIR_COMPARED_WWW_RT_IC = os.path.join(DIR_COMPARED_WWW_BSI_SITES, 'RT_IC')
DIR_COMPARED_RT_TPL = os.path.join(DIR_COMPARED, 'RT_TPL')
DIR_COMPARED_RTF = os.path.join(DIR_COMPARED, 'RTF')
DIR_COMPARED_RTF_BANK = os.path.join(DIR_COMPARED_RTF, 'Bank')
DIR_COMPARED_RTF_CLIENT = os.path.join(DIR_COMPARED_RTF, 'Client')
DIR_COMPARED_RTF_REPJET = os.path.join(DIR_COMPARED_RTF, 'RepJet')
DIR_COMPARED_XSD = os.path.join(DIR_COMPARED, 'XSD')
DIR_PATCH = os.path.join(DIR_TEMP, 'PATCH')


def dir_after_base(instance): 
    return os.path.join(DIR_AFTER, 'BASE', instance)


def dir_compared_base(instance): 
    return os.path.join(DIR_COMPARED, 'BASE', instance)

def dir_after_base_tables(instance): 
    return os.path.join(dir_after_base(instance), 'TABLES')

def dir_after_base_tabledata_config(instance): 
    return os.path.join(dir_after_base(instance), 'Table data', 'Config')

def dir_compared_bls(): 
    return os.path.join(DIR_COMPARED, 'BLS')

def dir_patch(instance=''): 
    return os.path.join(DIR_PATCH, instance)


def dir_patch_data(instance): 
    return os.path.join(dir_patch(instance), 'DATA')


def dir_patch_cbstart(instance, version=''): 
    return os.path.join(dir_patch(instance), f'CBSTART{version}')


def dir_patch_libfiles(instance, version=''): 
    return os.path.join(dir_patch(instance), f'LIBFILES{version}')


def dir_patch_libfiles_user(instance): 
    return os.path.join(dir_patch_libfiles(instance), 'USER')


def dir_patch_libfiles_source(): 
    return os.path.join(dir_patch_libfiles(INSTANCE_BANK), 'SOURCE')


def dir_patch_libfiles_bnk(version=''): 
    return os.path.join(dir_patch(INSTANCE_BANK), f'LIBFILES{version}.BNK')


def dir_patch_libfiles_bnk_add(version=''): 
    return os.path.join(dir_patch_libfiles_bnk(version), 'add')


def dir_patch_libfiles_bnk_bsiset_exe(version=''): 
    return os.path.join(dir_patch_libfiles_bnk(version), 'bsiset', 'EXE')


def dir_patch_libfiles_bnk_license_exe(version=''): 
    return os.path.join(dir_patch_libfiles_bnk(version), 'license', 'EXE')


def dir_patch_libfiles_bnk_rts(version=''): 
    return os.path.join(dir_patch_libfiles_bnk(version), 'rts')


def dir_patch_libfiles_bnk_rts_exe(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts(version), 'EXE')


def dir_patch_libfiles_bnk_rts_user(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts(version), 'USER')


def dir_patch_libfiles_bnk_rts_system(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts(version), 'SYSTEM')


def dir_patch_libfiles_bnk_rts_subsys(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts(version), 'SUBSYS')


def dir_patch_libfiles_bnk_rts_subsys_template(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys(version), 'TEMPLATE')


def dir_patch_libfiles_bnk_rts_subsys_instclnt(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys(version), 'INSTCLNT')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt(version), 'TEMPLATE')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template(version), 'DISTRIB')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib(version), 'CLIENT')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client(version), 'SUBSYS')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys(version), 'PRINT')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_rtf(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print(version), 'RTF')


def dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_repjet(version=''):
    return os.path.join(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print(version), 'RepJet')


def dir_patch_libfiles_bnk_www(version=''): 
    return os.path.join(dir_patch_libfiles_bnk(version), 'WWW')


def dir_patch_libfiles_bnk_www_exe(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www(version), 'EXE')


def dir_patch_libfiles_bnk_www_bsiscripts(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www(version),'BSI_scripts')


def dir_patch_libfiles_bnk_www_bsiscripts_rtic(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsiscripts(version), 'rt_ic')


def dir_patch_libfiles_bnk_www_bsiscripts_rtadmin(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsiscripts(version), 'rt_Admin')


def dir_patch_libfiles_bnk_www_bsiscripts_rtwa(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsiscripts(version), 'rt_wa')


def dir_patch_libfiles_bnk_www_bsisites(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www(version), 'BSI_sites')


def dir_patch_libfiles_bnk_www_bsisites_rtic(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites(version), 'rt_ic')


def dir_patch_libfiles_bnk_www_bsisites_rtwa(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites(version), 'rt_wa')


def dir_patch_libfiles_bnk_www_bsisites_rtic_code(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites_rtic(version), 'CODE')


def dir_patch_libfiles_bnk_www_bsisites_rtwa_code(version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites_rtwa(version), 'CODE')


def dir_patch_libfiles_bnk_www_bsisites_rtic_code_buildversion(build_version, version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites_rtic_code(version), build_version)


def dir_patch_libfiles_bnk_www_bsisites_rtwa_code_buildversion(build_version, version=''): 
    return os.path.join(dir_patch_libfiles_bnk_www_bsisites_rtwa_code(version), build_version)


def dir_patch_libfiles_exe(instance, version=''): 
    return os.path.join(dir_patch_libfiles(instance, version), 'EXE')


def dir_patch_libfiles_system(instance, version=''): 
    return os.path.join(dir_patch_libfiles(instance, version), 'SYSTEM')


def dir_patch_libfiles_subsys(instance, version=''): 
    return os.path.join(dir_patch_libfiles(instance, version), 'SUBSYS')


def dir_patch_libfiles_subsys_template(): 
    return os.path.join(dir_patch_libfiles_subsys(INSTANCE_BANK, ''), 'TEMPLATE')


def dir_patch_libfiles_subsys_print(instance, version=''): 
    return os.path.join(dir_patch_libfiles_subsys(instance, version), 'PRINT')


def dir_patch_libfiles_subsys_xsd(instance, version=''): 
    return os.path.join(dir_patch_libfiles_subsys(instance, version), 'XSD')


def dir_patch_libfiles_subsys_print_rtf(instance, version=''): 
    return os.path.join(dir_patch_libfiles_subsys_print(instance, version), 'RTF')


def dir_patch_libfiles_subsys_print_repjet(instance, version=''): 
    return os.path.join(dir_patch_libfiles_subsys_print(instance, version), 'RepJet')


def dir_patch_libfiles_instclnt(): 
    return os.path.join(dir_patch_libfiles_subsys(INSTANCE_BANK), 'INSTCLNT')


def dir_patch_libfiles_inettemp(): 
    return os.path.join(dir_patch_libfiles_instclnt(), 'INETTEMP')


def dir_patch_libfiles_template(): 
    return os.path.join(dir_patch_libfiles_instclnt(), 'TEMPLATE')


def dir_patch_libfiles_template_distribx(version): 
    return os.path.join(dir_patch_libfiles_template(), f'DISTRIB.X{version}')


def dir_patch_libfiles_template_distribx_client(version): 
    return os.path.join(dir_patch_libfiles_template_distribx(version), 'CLIENT')


def dir_patch_libfiles_template_distribx_client_exe(version): 
    return os.path.join(dir_patch_libfiles_template_distribx_client(version), 'EXE')


def dir_patch_libfiles_template_distribx_client_system(version): 
    return os.path.join(dir_patch_libfiles_template_distribx_client(version), 'SYSTEM')


def dir_patch_libfiles_template_languagex(version): 
    return os.path.join(dir_patch_libfiles_template(), f'Language.X{version}')


def dir_patch_libfiles_template_languagex_en(version): 
    return os.path.join(dir_patch_libfiles_template_languagex(version), 'ENGLISH')


def dir_patch_libfiles_template_languagex_ru(version): 
    return os.path.join(dir_patch_libfiles_template_languagex(version), 'RUSSIAN')


def dir_patch_libfiles_template_distrib(): 
    return os.path.join(dir_patch_libfiles_template(), 'DISTRIB')


def dir_patch_libfiles_template_distrib_client():
    return os.path.join(dir_patch_libfiles_template_distrib(), 'CLIENT')


def dir_patch_libfiles_template_distrib_client_exe():  
    return os.path.join(dir_patch_libfiles_template_distrib_client(), 'EXE')


def dir_patch_libfiles_template_distrib_client_system(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client(), 'SYSTEM')


def dir_patch_libfiles_template_distrib_client_subsys(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client(), 'SUBSYS')


def dir_patch_libfiles_template_distrib_client_subsys_print(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client_subsys(), 'PRINT')


def dir_patch_libfiles_template_distrib_client_subsys_print_rtf(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client_subsys_print(), 'RTF')


def dir_patch_libfiles_template_distrib_client_subsys_print_repjet(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client_subsys_print(), 'RepJet')


def dir_patch_libfiles_template_distrib_client_user(): 
    return os.path.join(dir_patch_libfiles_template_distrib_client(), 'USER')


def dir_patch_libfiles_template_language(): 
    return os.path.join(dir_patch_libfiles_template(), 'Language')


def dir_patch_libfiles_template_language_en(): 
    return os.path.join(dir_patch_libfiles_template_language(), 'ENGLISH')


def dir_patch_libfiles_template_language_ru(): 
    return os.path.join(dir_patch_libfiles_template_language(), 'RUSSIAN')


def dir_patch_libfiles_template_language_en_client_system(): 
    return os.path.join(dir_patch_libfiles_template_language(), 'ENGLISH', 'CLIENT', 'SYSTEM')


def dir_patch_libfiles_template_language_ru_client_system(): 
    return os.path.join(dir_patch_libfiles_template_language(), 'RUSSIAN', 'CLIENT', 'SYSTEM')


def get_filename_upgrade10_eif(instance): return os.path.join(dir_patch(instance), 'Upgrade(10).eif')


def get_filename_jira_tickets():
    return os.path.join(DIR_PATCH, 'jira_tickets.txt')


def dir_patch_libfilesreact():
    return os.path.join(dir_patch(INSTANCE_BANK), 'LIBFILES.REACT')


# -------------------------------------------------------------------------------------------------
def current_time_as_string(): return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


# -------------------------------------------------------------------------------------------------
def log(message_text):
    LOCK.acquire(True)
    try:
        log_file_name = os.path.join(os.path.abspath(''), filename('log'))
        with open(log_file_name, mode='a') as f:
            message_text = f'[{current_time_as_string()}][{threading.get_ident()}_{threading.current_thread().name}] {str(message_text)}'
            print(message_text)
            f.writelines('\n' + message_text)
    finally:
        LOCK.release()


def get_last_element_of_path(path):
    result = ''
    path = os.path.normpath(path)
    names = path.split(os.path.sep)
    if len(names):
        result = names[len(names) - 1]
    return result


def split_filename(path):
    result = ''
    if os.path.isfile(path):
        result = get_last_element_of_path(path)
    return result


def split_last_dir_name(path):
    result = ''
    if os.path.isdir(path):
        result = get_last_element_of_path(path)
    return result


UPGRADE10_HEADER = \
    "[SECTION]\n" \
    "Name = MAKEUPGRADE (10)\n" \
    "Type = DSPStructure\n" \
    "Version = 100\n" \
    "ObjectType = 10\n" \
    "ObjectName = MAKEUPGRADE\n" \
    "TableName = MakeUpgrade\n" \
    "ParentObject =\n" \
    "RootNode =\n" \
    "[DATA]\n" \
    " [REMARKS]\n" \
    "  V. Генератор апгрейдов\n" \
    " [TREE]\n" \
    "  Indexes\n" \
    "    AKey\n" \
    "      Fields\n" \
    "        AutoKey:integer = 0\n" \
    "      Unique:boolean = TRUE\n" \
    "      Primary:boolean = TRUE\n" \
    "    DSP\n" \
    "      Fields\n" \
    "        StructureType:integer = 0\n" \
    "        StructureName:integer = 1\n" \
    "  Fields\n" \
    "    AutoKey\n" \
    "      FieldType:integer = 14\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'PK'\n" \
    "    StructureType\n" \
    "      FieldType:integer = 1\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Категория'\n" \
    "    StructureName\n" \
    "      FieldType:integer = 0\n" \
    "      Length:integer = 255\n" \
    "      Remark:string = 'Структура'\n" \
    "    ImportStructure\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Импортировать или удалять структуру'\n" \
    "    BackupData\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Сохранять резервную копию структуры'\n" \
    "    ImportData\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Имп. данные или Локал. ресрсы для форм.'\n" \
    "    ReCreate\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Пересоздавать ли таблицу'\n" \
    "    NtClearRoot\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Очищать ветку структуры (данные таблицы) перед импортом'\n" \
    "    UpdateFound\n" \
    "      FieldType:integer = 16\n" \
    "      Length:integer = 0\n" \
    "      Remark:string = 'Обновлять сопадающие записи'\n" \
    "    IndexFields\n" \
    "      FieldType:integer = 8\n" \
    "      Length:integer = -1\n" \
    "      Remark:string = 'Список индексов полей для сравнения при добавлении записей (UpdateFound)'\n" \
    "    SubstFields\n" \
    "      FieldType:integer = 8\n" \
    "      Length:integer = -1\n" \
    "      Remark:string = 'Правила заполнения полей. (переименование, добавление поля в ПК...)'\n" \
    "    UseTransit\n" \
    "      FieldType:integer = 0\n" \
    "      Length:integer = 100\n" \
    "      Remark:string = 'Промежуточная структура'\n" \
    "    ParentFor\n" \
    "      FieldType:integer = 0\n" \
    "      Length:integer = 100\n" \
    "      Remark:string = 'Установить предком для структуры'\n" \
    "    OperationResult\n" \
    "      FieldType:integer = 0\n" \
    "      Length:integer = 255\n" \
    "      Remark:string = 'Результат операции'\n" \
    "    Description\n" \
    "      FieldType:integer = 0\n" \
    "      Length:integer = 255\n" \
    "      Remark:string = 'Описание операции'\n" \
    "[END]\n" \
    "[SECTION]\n" \
    "Name =  - Table data\n" \
    "Type = TableData\n" \
    "Version = 100\n" \
    "TableName = MAKEUPGRADE\n" \
    "[DATA]\n" \
    " [FIELDS]\n" \
    "  AutoKey\n" \
    "  StructureType\n" \
    "  StructureName\n" \
    "  ImportStructure\n" \
    "  BackupData\n" \
    "  ImportData\n" \
    "  ReCreate\n" \
    "  NtClearRoot\n" \
    "  UpdateFound\n" \
    "  IndexFields\n" \
    "  SubstFields\n" \
    "  UseTransit\n" \
    "  ParentFor\n" \
    "  OperationResult\n" \
    "  Description\n" \
    "[RECORDS]\n"

UPGRADE10_FOOTER = "[END]\n"
EXCLUDED_BUILD_FOR_BANK = ['autoupgr.exe', 'operedit.exe',
                        'crccons.exe', 'crprotst.exe',
                        'mbank.exe', 'memleak.exe',
                        'msysleak.exe', 'nsfilead.exe',
                        'nsservis.exe', 'nssrv.exe',
                        'nstcpad.exe',
                        'brhelper.exe', 'ctunnel.exe',
                        'defstart.exe', 'defupdt.exe',
                        'dosprot.exe',
                        'lang2htm.exe',
                        'licjoin.exe', 'lresedit.exe',
                        'bsledit.exe', 'bssiclogparser.exe',
                        'bssoapserver.exe', 'bsspluginhost.exe',
                        'bsspluginmanager.exe', 'bsspluginsetup.exe',
                        'bsspluginsetupnohost.exe', 'bsspluginwebkitsetup.exe',
                        'bssuinst.exe', 'cliex.exe',
                        'convertattaches.exe', 'copier.exe',
                        'ectrlsd.bpl', 'eif2base.exe',
                        'install.exe', 'lrescmp.exe',
                        'lreseif.exe', 'odbcmon.exe',
                        'abank.exe', 'alphalgn.exe',
                        'pbls.exe',
                        'rbtreed.bpl', 'rtoolsdt.bpl',
                        'pmonitor.bpl', 'pmonitor.exe',
                        'syneditd.bpl', 'updateic.exe',
                        'virtualtreesd.bpl', 'eif2base64_srv.exe',
                        'eif2base64_cli.dll', 'odbclog.dll',
                        'olha.dll', 'olha10.dll',
                        'olha9.dll', 'phemng.dll',
                        'pika.dll',
                        'authserv.exe',
                        'bsroute.exe', 'bssaxset.exe',
                        'bsdebug.exe', 'chngtree.exe',
                        'blstest.exe', 'ptchglue.exe', 'ptchhelp.exe',
                        'repcmd.exe', 'reqexec.exe',
                        'sysupgr.exe',
                        'testodbc.exe', 'testsign.exe',
                        'textrepl.exe', 'transtbl.exe',
                        'treeedit.exe', 'vbank.exe',
                        'verifyer.exe']

# todo убрать из клиента rg_*
const_excluded_build_for_CLIENT = EXCLUDED_BUILD_FOR_BANK + ['bsrdrct.exe',
                                                            'bsauthserver.exe',
                                                            'bsauthservice.exe',
                                                            'bsem.exe',
                                                            'cbank500.exe',
                                                            'gbank.exe',
                                                            'bsiset.exe',
                                                            'inetcfg.exe',
                                                            'bsmonitorserver.exe',
                                                            'bsmonitorservice.exe',
                                                            'btrdict.exe',
                                                            'cbserv.exe',
                                                            'combuff.exe',
                                                            'alphamon.exe',
                                                            'admin.exe',
                                                            'phoneserver.exe',
                                                            'phoneservice.exe',
                                                            'iniconf.exe',
                                                            'bsphone.bpl',
                                                            'phetools.bpl',
                                                            'infoserv.exe',
                                                            'infoservice.exe',
                                                            'bscc.exe',
                                                            'protcore.exe',
                                                            'rts.exe',
                                                            'rtsadmin.exe',
                                                            'rtsinfo.exe',
                                                            'rtsmbc.exe',
                                                            'rtsserv.exe',
                                                            'tcpagent.exe',
                                                            'BSSAxInf.exe',
                                                            'tredir.exe',
                                                            'upgr20i.exe',
                                                            'bsi.dll',
                                                            'cr_altok2x.dll',
                                                            'cr_ccm3x2x.dll',
                                                            'cr_epass2x.dll',
                                                            'cr_pass2x.dll',
                                                            'cr_sms2x.dll',
                                                            'dboblobtbl.dll',
                                                            'dbofileattach.dll',
                                                            'eif2base64_cli.dll',
                                                            'ilshield.dll',
                                                            'llazklnk.dll',
                                                            'llexctrl.dll',
                                                            'llrpjet2.dll',
                                                            'npbssplugin.dll',
                                                            'perfcontrol.dll',
                                                            'ptchmake.exe',
                                                            'updateal.exe',
                                                            'TranConv.exe',
                                                            'wwwgate.exe',
                                                            'TestTran.exe',
                                                            'infoinst.exe',
                                                            'gate_tst.exe',
                                                            'testconn.exe',
                                                            'etoknman.exe',
                                                            'stunnel.exe',
                                                            'defcfgup.exe',
                                                            'rxctl5.bpl',
                                                            'rtsrcfg.exe',
                                                            'rtsconst.exe',
                                                            'rtftobmp.exe',
                                                            'PtchMakeCl.exe',
                                                            'PrintServer.exe',
                                                            'phonelib.bpl',
                                                            'NewBase.exe',
                                                            'btrieve.bpl',
                                                            'mssobjs.bpl',
                                                            'bsslgn.exe',
                                                            'compiler.exe',
                                                            'VrfAgava.exe',
                                                            'BSSAxInf.exe',
                                                            'bsImport.exe',
                                                            'lresexpt.bpl',
                                                            'BSChecker.exe',
                                                            'bs1.exe',
                                                            'VerifCCom.exe',
                                                            'blksrv.bpl',
                                                            'bssetup.exe',
                                                            'aqtora32.dll',
                                                            'blocksrv.dll',
                                                            'rg_verb4.dll',
                                                            'rg_vesta.dll',
                                                            'cc.dll',
                                                            'ccom.dll',
                                                            'rg_vldt.dll',
                                                            'sendreq.dll',
                                                            'signcom.dll',
                                                            'TrConvL.dll',
                                                            'wsxml.dll',
                                                            'llmsshnd.dll',
                                                            'llmssobj.dll',
                                                            'llsocket.dll',
                                                            'llnetusr.dll',
                                                            'cr_epass.dll',
                                                            'llnotify.dll',
                                                            'llnsPars.dll',
                                                            'llnstool.dll',
                                                            'llPhone.dll',
                                                            'llPrReq.dll',
                                                            'llrrts.dll',
                                                            'ilCpyDocEx.dll',
                                                            'llrtscfg.dll',
                                                            'cr_pass.dll',
                                                            'cr_sms.dll',
                                                            'cr_util.dll',
                                                            'llsmpp.dll',
                                                            'llsnap.dll',
                                                            'llsonic.dll',
                                                            'devauth.dll',
                                                            'devcheck.dll',
                                                            'Dialogic.dll',
                                                            'llSRP.dll',
                                                            'eif2base.dll',
                                                            'Emulator.dll',
                                                            'LLSysInf.dll',
                                                            'GetIName.dll',
                                                            'lltblxml.dll',
                                                            'llTrAuth.dll',
                                                            'llTrServ.dll',
                                                            'llubstr.dll',
                                                            'llVTB.dll',
                                                            'llwebdav.dll',
                                                            'llwsexc.dll',
                                                            'llxml3ed.dll',
                                                            'llxmlcnz.dll',
                                                            'mig173.dll',
                                                            'mssreq.dll',
                                                            'notiflog.dll',
                                                            'rbaseal.dll',
                                                            'RBProxy.dll',
                                                            'rg_agava.dll',
                                                            'rg_altok.dll',
                                                            'rg_bsssl.dll',
                                                            'rg_call.dll',
                                                            'libcrypt.dll',
                                                            'rg_calus.dll',
                                                            'rg_ccm3e.dll',
                                                            'llamqdll.dll',
                                                            'rg_ccm3x.dll',
                                                            'rg_ccom2.dll',
                                                            'llCGate.dll',
                                                            'rg_clear.dll',
                                                            'rg_crypc.dll',
                                                            'rg_cryptfld.dll',
                                                            'rg_efssl.dll',
                                                            'rg_exc4.dll',
                                                            'rg_lite.dll',
                                                            'llmssreq.dll',
                                                            'lledint.dll',
                                                            'rg_msapi.dll',
                                                            'llepass.dll',
                                                            'rg_msp11.dll',
                                                            'rg_msp13.dll',
                                                            'llfraud.dll',
                                                            'llgraph.dll',
                                                            'llgraph1.dll',
                                                            'rg_msp2.dll',
                                                            'rg_mspex.dll',
                                                            'llhttp.dll',
                                                            'rg_ossl.dll'
                                                            ]


# -------------------------------------------------------------------------------------------------
def filename(ext):
    return f'{os.path.splitext(__file__)[0]}.{ext}'


# -------------------------------------------------------------------------------------------------
class GlobalSettings:
    def __init__(self):
        self.git_url = ''
        self.TagBefore = ''
        self.TagAfter = ''
        self.BuildAdditionalFolders = []
        self.BuildBK = ''
        self.BuildIC = ''
        self.BuildCrypto = ''
        self.PlaceBuildIntoPatchBK = False
        self.PlaceBuildIntoPatchIC = False
        self.ClientEverythingInEXE = False
        self.BuildRTSZIP = False
        self.LicenseServer = ''
        self.LicenseProfile = ''
        self.Is20Version = None
        self.BLLVersion = ''
        self.__success = False
        self.read_config()

    def was_success(self):
        return self.__success

    def read_config(self):
        ini_filename = filename('ini')
        section_special = 'SPECIAL'
        section_tags = 'TAGS'
        section_build = 'BUILD'
        try:
            if not os.path.exists(ini_filename):
                raise FileNotFoundError(f'NOT FOUND {ini_filename}')
            parser = configparser.RawConfigParser()
            res = parser.read(ini_filename, encoding="UTF-8")
            if res.count == 0:  # если файл настроек не найден
                raise FileNotFoundError(f'NOT FOUND {ini_filename}')

            self.git_url = parser.get(section_special, 'Git').strip()
            if not self.git_url:
                raise ValueError(f'NO Git defined in {ini_filename}')

            self.LicenseServer = parser.get(section_special, 'LicenseServer').strip()
            self.LicenseProfile = parser.get(section_special, 'LicenseProfile').strip()
            self.TagBefore = parser.get(section_tags, 'TagBefore').strip()
            self.TagAfter = parser.get(section_tags, 'TagAfter').strip()

            self.BuildAdditionalFolders = \
                [filepath.strip() for filepath in parser.get(section_build, 'ADDITIONAL').split(';')]
            self.BuildBK = parser.get(section_build, 'BK').strip()
            self.BuildIC = parser.get(section_build, 'IC').strip()
            self.BuildCrypto = parser.get(section_build, 'Crypto').strip()
            self.PlaceBuildIntoPatchBK = parser.get(section_build, 'PlaceBuildIntoPatchBK').lower() == 'true'
            self.PlaceBuildIntoPatchIC = parser.get(section_build, 'PlaceBuildIntoPatchIC').lower() == 'true'
            self.ClientEverythingInEXE = parser.get(section_special, 'ClientEverythingInEXE').lower() == 'true'
            self.BuildRTSZIP = parser.get(section_special, 'BuildRTSZIP').lower() == 'true'
            self.BLLVersion = parser.get(section_build, 'BLLVersion').strip()

            # проверка Labels -----------------------------------

            # проверка путей к билду
            if self.BuildBK and not os.path.exists(self.BuildBK):
                raise FileNotFoundError(f'NOT FOUND "{self.BuildBK}"')
            if self.BuildIC and not os.path.exists(self.BuildIC):
                raise FileNotFoundError(f'NOT FOUND "{self.BuildIC}"')

        except BaseException as exc:
            log(f'ERROR when reading settings from file "{ini_filename}":\n\t\t{exc}')

        else:
            self.__success = True
            log('SETTINGS LOADED:\n\t'
                f'Git = {self.git_url}\n\t'
                f'TagBefore = {self.TagBefore}\n\t'
                f'TagAfter = {self.TagAfter}\n\t'
                f'Licence server = {self.LicenseServer}\n\t'
                f'Licence profile = {self.LicenseProfile}\n\t'
                f'Build RTS.ZIP = {self.BuildRTSZIP}\n\t'
                f'Place BLL/DLL in EXE folder of Client patch = {self.ClientEverythingInEXE}\n\t'
                f'Place build files in patch = {self.PlaceBuildIntoPatchBK}\n\t'
                f'Place IC build files in patch = {self.PlaceBuildIntoPatchIC}\n\t'
                f'Path to additional build files = {self.BuildAdditionalFolders}\n\t'
                f'Path to build files = {self.BuildBK}\n\t'
                f'Path to IC build files = {self.BuildIC}\n\t'
                f'BLL version = {self.BLLVersion}')


# -------------------------------------------------------------------------------------------------
def get_password(message_text):
    import getpass
    # running under PyCharm or not
    if 'PYCHARM_HOSTED' in os.environ:
        return getpass.fallback_getpass(message_text)
    else:
        return getpass.getpass(message_text)


# -------------------------------------------------------------------------------------------------
def copy_tree(src, destination, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(destination):
            os.makedirs(destination)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                copy_tree(os.path.join(src, f),
                        os.path.join(destination, f),
                        ignore)
    else:
        shutil.copyfile(src, destination)


# -------------------------------------------------------------------------------------------------
def copy_file_or_dir(dir_name, file_name, destination, dirs_allowed=False):
    path = os.path.join(dir_name, file_name)
    if os.path.isfile(path):
        log(f'\tcopying {path}')
        make_dirs(destination)
        shutil.copy2(path, destination)
    else:
        if dirs_allowed:  
            log(f'\tcopying DIR with contents {path}')
            clean(os.path.join(destination, file_name))
            copy_tree(path, os.path.join(destination, file_name))
        else:
            log(f'\tsomething wrong {path} -> {destination}')

# -------------------------------------------------------------------------------------------------
def make_dirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except BaseException as exc:
        log(f'\tERROR: can''t create directory "{path}" ({exc})')


# -------------------------------------------------------------------------------------------------
def list_files_of_directory(path, mask):
    files_list = []
    for d, _, files in os.walk(path):
        for file_name in fnmatch.filter(files, mask):
            files_list.append(os.path.join(d, file_name))
        break  # чтобы прервать walk на первом же каталоге
    return sorted(files_list)


# -------------------------------------------------------------------------------------------------
def list_files_of_all_subdirectories(path, mask):
    files_list = [os.path.join(d, file_name) for d, _, files in os.walk(path)
                for file_name in fnmatch.filter(files, mask)]
    return sorted(files_list)


# -------------------------------------------------------------------------------------------------
def list_files_by_list(path, mask_list):
    res_list = []
    for mask in mask_list:
        res_list += [os.path.join(d, file_name) for d, _, files in os.walk(path)
                    for file_name in fnmatch.filter(files, mask)]
    return res_list


def replace_ext(file_name, new_ext):
    return os.path.splitext(file_name)[0] + new_ext


# -------------------------------------------------------------------------------------------------
def list_files_remove_paths_and_change_extension(path, new_ext, mask_list):
    return [replace_ext(bls_file, new_ext) for bls_file in
            [split_filename(bls_file) for bls_file in list_files_by_list(path, mask_list)]]


# -------------------------------------------------------------------------------------------------
# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=2, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    filled_length = int(round(bar_length * iteration / float(total)))
    percents = round(100.00 * (iteration / float(total)), decimals)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write('%s [%s] %s%s %s\r' % (prefix, bar, percents, '%', suffix)),
    sys.stdout.flush()
    if iteration == total:
        log("\n")


# -------------------------------------------------------------------------------------------------
def copy_files_ex(src_dir, destination_dir, function_to_list_files, wildcards=None, excluded_files=None):
    if wildcards is None:
        wildcards = ['*.*']
    if excluded_files is None:
        excluded_files = []
    for wildcard in wildcards:
        files = function_to_list_files(src_dir, wildcard)
        for filename_with_path in files:
            file_name = split_filename(filename_with_path)
            if file_name.lower() not in excluded_files and file_name != '.' and file_name != '..':
                make_dirs(destination_dir)
                try:
                    shutil.copy2(filename_with_path, destination_dir)
                except BaseException as exc:
                    log(f'\tERROR: can\'t copy file "{filename_with_path}" to "{destination_dir}" ({exc})')


# -------------------------------------------------------------------------------------------------
def copy_files_from_all_subdirectories(src_dir, destination_dir, wildcards=None, excluded_files=None):
    copy_files_ex(src_dir, destination_dir, list_files_of_all_subdirectories, wildcards, excluded_files)


# -------------------------------------------------------------------------------------------------
def copy_files_from_dir(src_dir, destination_dir, wildcards=None, excluded_files=None):
    copy_files_ex(src_dir, destination_dir, list_files_of_directory, wildcards, excluded_files)


# -------------------------------------------------------------------------------------------------
def copy_files_of_version(src_dir, destination_dir, exe_version, wildcards=None, excluded_files=None):
    if wildcards is None:
        wildcards = ['*.*']
    if excluded_files is None:
        excluded_files = []
    for wildcard in wildcards:
        files = list_files_of_all_subdirectories(src_dir, wildcard)
        for filename_with_path in files:
            file_name = split_filename(filename_with_path)
            if file_name.lower() not in excluded_files and file_name != '.' and file_name != '..':
                make_dirs(destination_dir)
                try:
                    if get_binary_platform(filename_with_path) == exe_version:
                        shutil.copy2(filename_with_path, destination_dir)
                except BaseException as exc:
                    log(f'\tERROR: can\'t copy file "{filename_with_path}" to "{destination_dir}" ({exc})')


# -------------------------------------------------------------------------------------------------
def quote(string2prepare):
    return "\"" + string2prepare + "\""


# -------------------------------------------------------------------------------------------------
# Очистка рабочих каталогов
def __onerror_handler__(func, path):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    # if not os.access(path, os.W_OK):
    # Is the error an access error ?
    os.chmod(path, stat.S_IWRITE)
    os.chmod(path, stat.S_IWUSR)
    func(path)
    # else:
    #   raise BaseException(exc_info)


# -------------------------------------------------------------------------------------------------
def clean(path, masks=None):
    if os.path.exists(path):
        try:
            if masks:
                log(f'CLEANING {path} for {masks} files')
                for mask in masks:
                    # чистим все файлы по маске mask
                    [os.remove(os.path.join(d, file_name)) for d, _, files in os.walk(path) for file_name in
                    fnmatch.filter(files, mask)]
            else:
                log(f'CLEANING {path}')
                # Сначала чистим все файлы,
                [os.remove(os.path.join(d, file_name)) for d, _, files in os.walk(path) for file_name in files]
                # потом чистим все
                shutil.rmtree(path, onerror=__onerror_handler__)
        except FileNotFoundError:
            pass  # если папка отсутствует, то продолжаем молча
        except BaseException as exc:
            log(f'\tERROR when cleaning ({exc})')
            return False
    return True


# -------------------------------------------------------------------------------------------------
def download_repo_from_git(git_url, repo_path, tag):
    git_repo = Repo.init(repo_path)
    origin = git_repo.create_remote('origin', git_url)
    exists = origin.exists()
    if exists:
        origin.fetch()
        if tag not in git_repo.tags:
            log(f'Not found tag "{tag}" in remote tags: {git_repo.tags}')
            return False
        git = git_repo.git
        git.checkout(git_repo.tags[tag])
        return True
    else:
        return False


# -------------------------------------------------------------------------------------------------
def download_git_thread(git_tag_info):
    log(f'Downloading from remote {git_tag_info}')
    if download_repo_from_git(git_tag_info['git_url'], git_tag_info['local_path'], git_tag_info['git_tag']):
        git_tag = git_tag_info['git_tag']
        log(f'Successfully downloaded tag "{git_tag}"')
        return True
    else:
        git_tag = git_tag_info['git_tag']
        log(f'Error when tried to download tag "{git_tag}"')
        return False


# -------------------------------------------------------------------------------------------------
def download_from_git(settings):
    log('GIT DOWNLOAD BEGIN')
    git_tags_info = [{'git_tag': settings.TagBefore, 'git_url': settings.git_url, 'local_path': DIR_BEFORE},
                    {'git_tag': settings.TagAfter, 'git_url': settings.git_url, 'local_path': DIR_AFTER}]
    futures = []
    for git_tag_info in git_tags_info:
        futures.append(EXECUTOR.submit(download_git_thread, git_tag_info))
    done, not_done = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)
    total_result = True
    for future in concurrent.futures.as_completed(done):
        try:
            result = future.result()
            total_result = total_result and result
        except Exception as exc:
            log(f'Thread generated an exception: {exc}')
            total_result = False
    log(f'GIT DOWNLOAD FINISHED with result {total_result}')
    return total_result


# -------------------------------------------------------------------------------------------------
def __compare_and_copy_dirs_recursively__(before, after, where_to_copy):
    dircmp = filecmp.dircmp(before, after)
    if dircmp.common_dirs:
        for directory in dircmp.common_dirs:
            __compare_and_copy_dirs_recursively__(os.path.join(before, directory),
                                                os.path.join(after, directory),
                                                os.path.join(where_to_copy, directory))

    if len(dircmp.diff_files):
        for file in dircmp.diff_files:
            copy_file_or_dir(after, file, where_to_copy)
    
    if dircmp.same_files:
        match, mismatch, errors = filecmp.cmpfiles(before, after, dircmp.same_files, shallow=False)
        if mismatch:
            for file in mismatch:
                copy_file_or_dir(after, file, where_to_copy)

    if dircmp.right_only:
        for file_or_dir in dircmp.right_only:
            copy_file_or_dir(after, file_or_dir, where_to_copy, True)


# -------------------------------------------------------------------------------------------------
def compare_directories_before_and_after():
    if os.path.exists(DIR_BEFORE):
        log('BEGIN compare directories:')
        log(f'\tBEFORE: {DIR_BEFORE}')
        log(f'\tAFTER:  {DIR_AFTER}')
        begin_time = time.time()
        __compare_and_copy_dirs_recursively__(DIR_BEFORE, DIR_AFTER, DIR_COMPARED)
        log(f'COMPARED for {datetime.timedelta(seconds = time.time()-begin_time)} minutes')
    else:
        os.rename(DIR_AFTER, DIR_COMPARED)
        log('\tUSING folder "AFTER" as compare result, because "BEFORE" not exists:')
        log(f'\tBEFORE (not exists): {DIR_BEFORE}')
        log(f'\tAFTER              : {DIR_AFTER}')
    if os.path.exists(DIR_COMPARED):
        log(f'\tFINISHED compare directories. LOOK at {DIR_COMPARED}')
        return True
    else:
        log('\tFINISHED compare directories. NO CHANGES!!!')
        return False


# -------------------------------------------------------------------------------------------------
def make_upgrade10_eif_string_for_tables(file_name):
    file_name_lower = file_name.lower()

    # Для дефолтных таблиц и таблиц в памяти
    if file_name_lower.endswith('default') or \
            file_name_lower.startswith('root') or \
            file_name_lower == 'customeroldrpl' or \
            file_name_lower == 'memorydiasoftbuf':
        result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'>"

    elif file_name.find(".") > 0:  # Для блобов
        result = "<{}|{}|'{}'|TRUE|FALSE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'>"
    # загружить как дефолтную, но обязательно обновлять bls-кой
    elif file_name_lower == 'bs3kvit':
        result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'> #TODO: ДОЛЖЕН БЫТЬ ВЫЗОВ ua-шки"
    # обновление дельтой
    elif file_name_lower == 'orderstartflag':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'Flag'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'docschemesettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ID'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'docprintsettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'BranchID,CustId,SchemeId'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'docmultiprintsettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'SchemeID,PrintFormName'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'filtersettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ScrollerName'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'linktxt':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'NameFormat'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'absmanagertype':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|FALSE|TRUE|TRUE|'ID'|NULL|NULL|NULL|NULL|'Таблицы'>" #TODO обязательно дельту"
    elif file_name_lower == 'checkparams':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|FALSE|TRUE|TRUE|'FilterID,ParamIndex'|NULL|NULL|NULL|NULL|'Таблицы'>" #TODO обязательно дельту"    
    elif file_name_lower == 'dcmversions':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'SchemeID,PatchNewVersion'|NULL|NULL|NULL|NULL|'Таблицы'>"
    elif file_name_lower == 'transschema':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ConnType,SchemaName'|NULL|NULL|NULL|NULL|'Таблицы'>"
    elif file_name_lower == 'remotenavmenus':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ID'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO проверьте data таблицы"
    elif file_name_lower == 'remotenavtrees':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ID'|NULL|NULL|NULL|NULL|'Таблицы'> " \
                "#TODO проверьте data таблицы, обновлять нужно только эталонное дерево"
    elif file_name_lower == 'offersettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'Autokey'|NULL|NULL|NULL|NULL|'Таблицы'>"
    elif file_name_lower == 'armabcode':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'Code'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO обязательно дельту"
    elif file_name_lower == 'systemlogcodeset':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'TransactionType'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO обязательно дельту"
    elif file_name_lower == 'smssettings':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'ID,SchemeId'|NULL|NULL|NULL|NULL|'Таблицы'> #TODO обязательно дельту"

    # пересоздание
    elif file_name_lower == 'postclnt':
        result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|TRUE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'>"

    # полностью заменяющиеся данные:
    elif file_name_lower == 'noticeconfig' or file_name_lower == 'paygrndparam' or \
            file_name_lower == 'mailreport' or file_name_lower == 'wanavtrees' or \
            file_name_lower == 'balaccountsettings' or file_name_lower == 'rkobranches' or \
            file_name_lower == 'mb2_versionsinfo' or file_name_lower == 'mb_remotecfg' or \
            file_name_lower == 'nocopydocfields' or file_name_lower == 'mbamsgxmlstructure' or \
            file_name_lower == 'mbamsgscheme' or file_name_lower == 'mbamsgdocstatus' or \
            file_name_lower == 'mbadocumentssettings' or file_name_lower == 'azkestimate':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'>"
    elif file_name_lower == 'remotepasscfg':
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'> " \
                "#TODO: скорее всего, нельзя оставлять эту таблицу в патче!!!"
    elif file_name_lower == 'controlgroups': #file_name_lower == 'controlsettings' or file_name_lower == 'controlconstants' or 
        result = "<{}|{}|'{}'|  ДОЛЖЕН БЫТЬ ВЫЗОВ uaControls или другой ua-шки  >"
    elif file_name_lower == 'remoterolesactions' or \
            file_name_lower == 'remoterolesdocsettings':
        result = "<{}|{}|'{}'|  ДОЛЖЕН БЫТЬ один ВЫЗОВ ubRoles, в этой data нужно оставить " \
                "дельту изменений remoterolesactions можно оставить полностью>"
    elif file_name_lower.startswith('bs3'):
        result = "<{}|{}|'{}'|  ДОЛЖЕН БЫТЬ ВЫЗОВ ua-шки  >"
    elif file_name_lower == 'freedoctype':
        result = "<{}|{}|'{}'|  ДОЛЖЕН БЫТЬ ВЫЗОВ ua-шки  >"
    else:  # Если заливается структура полностью
        result = "<{}|{}|'{}'|TRUE|TRUE|TRUE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Таблицы'> " \
                "#TODO проверьте способ обновления таблицы, сейчас - заливается полностью. " \
                "Для дельты и обновления строк: |TRUE|TRUE|TRUE|TRUE|TRUE|TRUE|'название_полей'. " \
                "Только заменить структуру десятки: |TRUE|FALSE|FALSE|FALSE|TRUE|FALSE|NULL. " \
                "Заменить структуру и пересоздать: |TRUE|TRUE|FALSE|TRUE|TRUE|FALSE|NULL."
    return result


# -------------------------------------------------------------------------------------------------
def upgrade10_eif_by_file_name(counter, file_name):
    if file_name.lower() == 'version(14).eif':  # идите на хуй https://jira.bssys.com/browse/GPBDBOPE-18
        return f"  <{counter}|14|'Version'|TRUE|TRUE|FALSE|FALSE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Конфигурации'> #TODO проверьте настройку\n"

    result = ''
    file_type_match = re.findall(r'\((?:\d+|data)\)\.eif', file_name, flags=re.IGNORECASE)
    if len(file_type_match):
        structure_type_raw = file_type_match[0]
        structure_type = re.sub(r'\.eif', '', structure_type_raw, flags=re.IGNORECASE).replace('(', '').replace(')', '')
        if structure_type.upper() == 'DATA':
            return ''  # пропускаем data-файлы, за них ответят 10-файлы
        file_name = file_name.replace(structure_type_raw, '')
        if structure_type == '10':
            result = make_upgrade10_eif_string_for_tables(file_name)
        elif structure_type == '12':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|NULL|'Визуальные формы'>"
        elif structure_type == '14':  # идите на хуй https://jira.bssys.com/browse/GPBDBOPE-18
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|TRUE|FALSE|NULL|NULL|NULL|NULL|NULL|'Конфигурации'> " \
                    "#TODO проверьте настройку / существующие ветки не обновляются, смотри https://jira.bssys.com/browse/GPBDBOPE-18"
        elif structure_type == '16':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|NULL|'Автопроцедуры'>"
        elif structure_type == '18':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Профили'>"
        elif structure_type == '19':
            result = "<{}|{}|'{}'|TRUE|FALSE|FALSE|TRUE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Роли'>"
        elif structure_type == '20':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Привилегии'>"
        elif structure_type == '21':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Пользователи'>"
        elif structure_type == '30':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|NULL|'Сценарии'>"
        elif structure_type == '65':
            if file_name.lower() == 'subsys' or file_name.lower() == 'mbsc2':
                result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'RTS SUBSYS(65)'> " \
                        "#TODO проверьте настройку"
            else:
                result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'RTS(65)'>"
        elif structure_type == '66':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|TRUE|NULL|NULL|NULL|NULL|NULL|'RTS Errors/Tasks params'>"
        elif structure_type == '71':
            result = "<{}|{}|'{}'|TRUE|FALSE|FALSE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Генераторы'>"
        elif structure_type == '72':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Структуры отображений'>"
        elif structure_type == '73':
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|TRUE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Хранимые процедуры'>"
        elif structure_type in ['50', '81']:
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Простые операции'>"
        elif structure_type in ['51', '82']:
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Табличные операции'>"
        elif structure_type in ['52', '83']:
            result = "<{}|{}|'{}'|TRUE|TRUE|FALSE|FALSE|FALSE|FALSE|NULL|NULL|NULL|NULL|NULL|'Документарные операции'>"
        elif structure_type == '84':
            result = "<{}|{}|'{}'|TRUE|FALSE|FALSE|TRUE|TRUE|TRUE|NULL|NULL|NULL|NULL|NULL|'Статусы'>"
        else:
            log(f'\tERROR unknown structure type {structure_type} for filename {file_name}')

        return '  ' + result.format(counter, structure_type, file_name) + '\n'
    else:
        log(f'\tERROR can not detect structure type by filename ({file_name})')


# -------------------------------------------------------------------------------------------------
def copy_table_10_files_for_data_files(instance):
    eif_list = list_files_of_all_subdirectories(dir_compared_base(instance), "*.eif")
    for eif_file in eif_list:
        # проверим соответствует ли название файла формату "*(data).eif"
        file_type_match = re.findall(r'\(data\)\.eif', eif_file, flags=re.IGNORECASE)
        if len(file_type_match):
            eif10_file = str(eif_file).replace(file_type_match[0], '(10).eif')
            # отрежем путь (splitfilename не пашет, если файла нет)
            eif10_file = get_last_element_of_path(eif10_file)
            # и проверим есть ли файл eif10_file в списке файлов eif_list
            exists = [file1 for file1 in eif_list if re.search(re.escape(eif10_file), file1)]
            if not exists:
                source_dir = os.path.join(dir_after_base(instance), 'TABLES')
                dest_dir = os.path.join(dir_compared_base(instance), 'TABLES')
                log(f'COPYING {eif10_file} from {source_dir} to {dest_dir}')
                copy_files_from_dir(source_dir, dest_dir, [eif10_file])


# -------------------------------------------------------------------------------------------------
def upgrade10_ua_bls_files(instance, counter, lines):
    mask = ''
    if instance==INSTANCE_BANK:
        mask = 'u[ab]*.bls'
    elif instance in [INSTANCE_CLIENT, INSTANCE_CLIENT_MBA]:
        mask = 'u[ac]*.bls'
    else: 
        raise(f'Unknown instance {instance}')

    ua_bls_list = list_files_of_all_subdirectories(dir_compared_bls(), mask)
    for file_path in ua_bls_list:
        file_name = split_filename(file_path).lower()
        if file_name not in ['ualib.bls', 'uacontrols.bls', 'uacustjb.bls']:
            exports = bls_get_exports(file_path)
            for function_name in exports:
                bll_file_name = replace_ext(file_name, '.bll')
                log(f'ADDING to {instance} launch {bll_file_name}.{function_name} launch in upgrade(10).eif')
                lines.append(f"  <{counter}|200|NULL|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|'{function_name}'|NULL|'{bll_file_name}'|NULL|'Запуск {function_name}({bll_file_name})'>\n")
                counter += 1
    return counter


# -------------------------------------------------------------------------------------------------
def upgrade10_controls(instance, counter, lines):
    dir_tables = dir_after_base_tables(instance)
    dir_data = dir_after_base_tabledata_config(instance)
    patch_data_dir = dir_patch_data(instance)
    control_groups = list_files_of_all_subdirectories(dir_compared_base(instance), 'CONTROLGROUPS(data).eif')
    control_constants = list_files_of_all_subdirectories(dir_compared_base(instance), 'CONTROLCONSTANTS(data).eif')
    control_settings = list_files_of_all_subdirectories(dir_compared_base(instance), 'CONTROLSETTINGS(data).eif')

    if len(control_settings) or len(control_constants):
        copy_files_from_dir(dir_tables, patch_data_dir, ['CONTROLGROUPS(10).eif'])
        if not len(control_groups):
            copy_files_from_dir(dir_data, patch_data_dir, ['CONTROLGROUPS(data).eif'])

    if len(control_settings):
        copy_files_from_dir(dir_tables, patch_data_dir, ['CONTROLSETTINGS(10).eif', 'CONTROLCONSTANTS(10).eif'])
        if not(control_constants):
            copy_files_from_dir(dir_data, patch_data_dir, ['CONTROLCONSTANTS(data).eif'])
    elif len(control_constants):
        copy_files_from_dir(dir_tables, patch_data_dir, ['CONTROLSETTINGS(10).eif', 'CONTROLCONSTANTS(10).eif'])
        if not len(control_settings):
            copy_files_from_dir(dir_data, patch_data_dir, ['CONTROLSETTINGS(data).eif'])

    if len(control_settings) or len(control_constants):
        lines.append(f"  <{counter}|200|NULL|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|'BackUpControls'|NULL|'uaControls.BLL'|NULL|'Запуск BackUpControls(uaControls)'>\n")
        counter += 1
        lines.append(f"  <{counter}|200|NULL|TRUE|FALSE|TRUE|NULL|NULL|NULL|NULL|'SetupControls'|NULL|'uaControls.bll'|NULL|'Запуск SetupControls(uaControls)'>\n")
        counter += 1
        lines.append(f"  <{counter}|200|NULL|FALSE|TRUE|TRUE|NULL|NULL|NULL|NULL|'RestoreControls'|NULL|'uaControls.bll'|NULL|'Запуск RestoreControls(uaControls)'>\n")

    return counter


# -------------------------------------------------------------------------------------------------
def upgrade10_db_structures(instance, counter, lines):
    lines.append(upgrade10_eif_by_file_name(counter, 'Version(14).eif'))
    counter += 1
    patch_data_dir = dir_patch_data(instance)
    eif_list = list_files_of_all_subdirectories(patch_data_dir, '*.eif')
    for eif_file in eif_list:
        eif_file_name = split_filename(eif_file)
        line = upgrade10_eif_by_file_name(counter, eif_file_name)
        if line:
            lines.append(line)
            counter += 1
    return counter


# -------------------------------------------------------------------------------------------------
def upgrade10_react_build(instance, counter, lines):
    if instance==INSTANCE_BANK:
        if os.path.exists(DIR_COMPARED_WWW_react):
            lines.append('  TODO: НУЖНА СБОРКА РЕДИЗАЙНА!!!\n')
            counter +=1
    return counter


# -------------------------------------------------------------------------------------------------
def upgrade10_eif(instance):
    patch_data_dir = dir_patch_data(instance)
    make_dirs(patch_data_dir)
    copy_files_from_all_subdirectories(dir_compared_base(instance), patch_data_dir, ['*.eif'])
    
    lines = []
    lines.append(UPGRADE10_HEADER)
    counter = 1
    counter = upgrade10_db_structures(instance, counter, lines)
    counter = upgrade10_ua_bls_files(instance, counter, lines)
    counter = upgrade10_controls(instance, counter, lines)
    counter = upgrade10_react_build(instance, counter, lines)

    with open(get_filename_upgrade10_eif(instance), mode='w') as f:
        f.writelines(lines)
        f.writelines(UPGRADE10_FOOTER)


# -------------------------------------------------------------------------------------------------
def get_version_from_win32_pe(file):
    # http://windowssdk.msdn.microsoft.com/en-us/library/ms646997.aspx
    sig = struct.pack("32s", u"VS_VERSION_INFO".encode("utf-16-le"))
    # This pulls the whole file into memory, so not very feasible for
    # large binaries.
    try:
        file_data = open(file).read()
    except IOError or FileNotFoundError:
        return "Unknown"
    offset = file_data.find(str(sig))
    if offset == -1:
        return "Unknown"

    file_data = b''
    file_data = file_data[offset + 32: offset + 32 + (13 * 4)]
    version_structure = struct.unpack("13I", file_data)
    ver_ms, ver_ls = version_structure[4], version_structure[5]
    return "%d.%d.%d.%d" % (ver_ls & 0x0000ffff, (ver_ms & 0xffff0000) >> 16,
                            ver_ms & 0x0000ffff, (ver_ls & 0xffff0000) >> 16)


# -------------------------------------------------------------------------------------------------
def get_binary_platform(full_file_path):
    image_file_machine_i386 = 332
    image_file_machine_ia64 = 512
    image_file_machine_amd64 = 34404

    try:
        with open(full_file_path, 'rb') as f:
            s = f.read(2).decode(encoding="utf-8", errors="strict")
            if s != "MZ":
                return None
                # log("Not an EXE file")
            else:
                f.seek(60)
                s = f.read(4)
                header_offset = struct.unpack("<L", s)[0]
                f.seek(header_offset + 4)
                s = f.read(2)
                machine = struct.unpack("<H", s)[0]

                if machine == image_file_machine_i386:
                    return "Win32"
                    # log("IA-32 (32-bit x86)")
                elif machine == image_file_machine_ia64:
                    return "Win64"
                    # log("IA-64 (Itanium)")
                elif machine == image_file_machine_amd64:
                    return "Win64"
                    # log("AMD64 (64-bit x86)")
                else:
                    return "Unknown"
                    # log("Unknown architecture")
    except IOError or FileNotFoundError:
        return None


# -------------------------------------------------------------------------------------------------
def __get_exe_file_info__(full_file_path):
    # http://windowssdk.msdn.microsoft.com/en-us/library/ms646997.aspx
    sig = struct.pack("32s", u"VS_VERSION_INFO".encode("utf-16-le"))
    # This pulls the whole file into memory, so not very feasible for
    # large binaries.
    try:
        with open(full_file_path, 'rb') as f:
            file_data = f.read()
    except IOError or FileNotFoundError:
        return None
    offset = file_data.find(sig)
    if offset == -1:
        return None

    file_data = file_data[offset + 32: offset + 32 + (13 * 4)]
    version_structure = struct.unpack("13I", file_data)
    ver_ms, ver_ls = version_structure[4], version_structure[5]
    return "%d.%d.%d.%d" % (ver_ls & 0x0000ffff, (ver_ms & 0xffff0000) >> 16,
                            ver_ms & 0x0000ffff, (ver_ls & 0xffff0000) >> 16)


# -------------------------------------------------------------------------------------------------
def extract_build_version(build_path):
    result = 'unknown'
    try:
        if os.path.exists(build_path):
            files = list_files_of_all_subdirectories(build_path, 'cbank.exe')
            files += list_files_of_all_subdirectories(build_path, 'BRHelper.exe')
            files += list_files_of_all_subdirectories(build_path, 'cryptlib2x.dll')
            files += list_files_of_all_subdirectories(build_path, 'npBSSPlugin.dll')
            files += list_files_of_all_subdirectories(build_path, 'CryptLib.dll')
            for f in files:
                ver = None
                try:
                    ver = __get_exe_file_info__(f)
                except IOError or FileNotFoundError:
                    pass
                # отладочный билд имеет кривую версию, нужно пропустить
                if (ver is not None) and (ver != '1.0.0.0') and (ver != '0.0.0.0'):
                    result = ver
                    break

    except BaseException as exc:
        log(f'\tERROR: can not detect version of build ({exc})')
        raise e
    return result


# -------------------------------------------------------------------------------------------------
def open_encoding_aware(path):
    encodings = ['windows-1251', 'utf-8']
    for enc in encodings:
        try:
            fh = open(path, 'r', encoding=enc)
            fh.readlines()
            fh.seek(0)
        except ValueError:
            pass
        else:
            return fh
    return None


# -------------------------------------------------------------------------------------------------Z
def __replace_unwanted_symbols__(pattern, string):
    find_all = re.findall(pattern, string, flags=re.MULTILINE)
    for find_here in find_all:
        string = string.replace(find_here, '')
    return string


# -------------------------------------------------------------------------------------------------Z
def replace_unwanted_symbols(text):
    # удаляем комментарии, которые располагаются между фигурными скобками "{ .. }"
    text = __replace_unwanted_symbols__(r'{[\S\s]*?}', text)
    # удаляем комментарии, которые располагаются между скобками "(* .. *)"
    text = __replace_unwanted_symbols__(r'\(\*[\S\s]*?\*\)', text)
    # удаляем однострочные комментарии, которые начинаются на "//"
    return __replace_unwanted_symbols__(r'//.*', text)
    

# -------------------------------------------------------------------------------------------------
def bls_get_exports(file_name):
    with open_encoding_aware(file_name) as f:
        if f:
            text = replace_unwanted_symbols(f.read())
            # находим текст между словом "exports" и ближайшей точкой с запятой
            return [fn.strip() for fn in re.findall(r'(?s)(?<=\bexports\s)(.*?)(?=;)', text, flags=re.IGNORECASE)]


# -------------------------------------------------------------------------------------------------
def bls_get_uses_graph(file_name, compiled_list, bls_uses_graph):
    file_name_and_dir = os.path.split(os.path.abspath(file_name))
    file_name_without_path = file_name_and_dir[1].lower()
    file_dir = file_name_and_dir[0]
    with open_encoding_aware(file_name) as f:
        if f:
            text = replace_unwanted_symbols(f.read())
            # находим текст между словом "uses" и ближайшей точкой с запятой
            list_of_uses = re.findall(r'(?s)(?<=\buses\s)(.*?)(?=;)', text, flags=re.IGNORECASE)
            
            # добавляем пустой элемент для файла "file_name", на случай, если файл не имеет uses
            bls_uses_graph.update({file_name_without_path: [file_name, []]})

            if len(list_of_uses):
                for text_of_uses in list_of_uses:
                    # разбиваем найденный текст на части между запятыми
                    uses_list = [line.strip().lower() + '.bls' for line in text_of_uses.split(',') if line.strip()]
                    if uses_list:
                        # проверим, что такой файл еще не был обработан

                        item_already_in_list = bls_uses_graph.get(file_name_without_path)
                        # если элемент с названием "file_name_without_path" уже есть в списке bls_uses_graph
                        if item_already_in_list:
                            # то дополним его [список_зависимостей] списком "uses_list"
                            item_already_in_list[1].extend(uses_list)
                        else:
                            # TODO: ЭТА ВЕТКА НЕ НУЖНА, НАДО УДАЛИТЬ (ВЫШЕ УЖЕ ДОБАВЛЯЮ ПУСТОЙ ЭЛЕМЕНТ)
                            # если файла нет в списке зависимостей,
                            # то добавим "{название_файла: [полное_название_с_путем, [список_зависимостей]]}"
                            # bls_uses_graph.update({file_name_without_path: [file_name, uses_list]})
                            pass
                        
                        for uses_item in uses_list:
                            item_already_in_list = bls_uses_graph.get(uses_item)
                            item_already_compiled = uses_item in compiled_list
                            if not item_already_in_list and not item_already_compiled:
                                bls_get_uses_graph(os.path.join(file_dir, uses_item), compiled_list, bls_uses_graph)
    return bls_uses_graph


# -------------------------------------------------------------------------------------------------
def compile_one_file(build_path, bls_file_name, bls_path, uses_list, lic_server, lic_profile, version, failed_files, percents_to_log):
    # проверим, есть ли компилятор
    bscc_path = os.path.join(build_path, 'bscc.exe')
    if not os.path.exists(bscc_path):
        # компилятора нет, ошибка
        raise FileNotFoundError(f'Compiler {bscc_path} not found')
    run_str = bscc_path + f' "{bls_path}" -M0 -O0 -S{lic_server} -A{lic_profile} -R1'
    if version:
        run_str = run_str + f' -V"{version}"'

    log("\t{:>3}%".format(percents_to_log) + '\t' + bls_file_name)
    process = subprocess.Popen(run_str, shell=False, stdout=subprocess.PIPE)  # , stderr=subprocess.PIPE
    out, err = process.communicate()
    process.stdout.close()
    str_res = '\n\t\t\t' + out.decode('windows-1251').replace('\n', '\n\t\t\t')
    # !!! successfully с ошибкой. так и должно быть !!!
    if 'Compiled succesfully' not in str_res and 'Compiled with warnings' not in str_res:
        if bls_file_name not in failed_files:
            failed_files.append(bls_file_name)
        log(f'\tERROR: File "{bls_file_name}", Uses list "{uses_list}"{str_res}')
        log('\tCOMPILATION continues. Please wait...')
        return False
    else:
        return True


# -------------------------------------------------------------------------------------------------
def file_compiled(bls_file_name, compiled_list):
    with LOCK:
        return bls_file_name in compiled_list


# -------------------------------------------------------------------------------------------------
def compile_recursive(lic_server, lic_profile, build_path, bls_uses_graph, bls_file_name, 
                            compiling_now_list, compiled_list, files_count, bll_version, failed_files):
    
    bls_file_name = bls_file_name.lower()

    with CONDITION:
        while bls_file_name in compiling_now_list:
            CONDITION.wait()
        compiling_now_list.append(bls_file_name)

    try:
        if file_compiled(bls_file_name, compiled_list):
            # если файл уже откомпилирован
            return

        bls_item_info = bls_uses_graph.get(bls_file_name)
        if not bls_item_info:
            log(f'No information about file to compile "{bls_file_name}". Probably not all SOURCE were downloaded.')
            return

        bls_file_path = bls_item_info[0]
        uses_list = bls_item_info[1]
        
        if len(uses_list):  # если файл зависит от других файлов, то проведем
            for uses_file_name in uses_list:  # компиляцию каждого файла
                # рекурсия, компилируем список зависимостей:
                compile_recursive(lic_server,
                                lic_profile,
                                build_path,
                                bls_uses_graph,
                                uses_file_name,
                                compiling_now_list,
                                compiled_list,
                                files_count,
                                bll_version,
                                failed_files)
            
        percents = int(100.00 * len(compiled_list) / files_count)
        if compile_one_file(build_path, bls_file_name, bls_file_path,
                        uses_list, lic_server, lic_profile, bll_version,
                        failed_files, percents):
            compiled_list.append(bls_file_name)  # добавляем в список учтенных файлов
    
    finally:
        with CONDITION:
            compiling_now_list.remove(bls_file_name)
            CONDITION.notify_all()


# -------------------------------------------------------------------------------------------------
def compile_thread_function(lic_server, lic_profile, build_path, file_name, compiling_now_list, compiled_list, files_count, bll_version, failed_files):
    if file_compiled(file_name, compiled_list):
        return
    
    bls_uses_graph = {}

    bls_get_uses_graph(file_name, compiled_list, bls_uses_graph)  # строим граф зависимостей по строкам uses    
    try:
        for bls_file_name in bls_uses_graph:  # компилируем все bls
            compile_recursive(lic_server, lic_profile, build_path, bls_uses_graph,
                                            bls_file_name, compiling_now_list, compiled_list, files_count, bll_version, failed_files)
    except FileNotFoundError as exc:
        log(f'\tERROR: {exc}')


# -------------------------------------------------------------------------------------------------
def compile_all(lic_server, lic_profile, build_path, source_path, bll_version):
    clean(build_path, ['*.bls', '*.bll', '*.ClassInfo'])  # очищаем каталог билда от bls и bll
    begin_time = time.time()
    log('BEGIN BLS COMPILATION. Please wait...')
    copy_files_from_all_subdirectories(source_path, build_path, ['*.bls'])  # копируем в каталог билда все bls

    compiling_now_list = []
    compiled_list = []
    failed_files = []
    futures = []
    files = list_files_of_all_subdirectories(build_path, '*.bls')
    files_count = len(files)
    for file_name in files:
        futures.append(EXECUTOR.submit(compile_thread_function, lic_server, lic_profile, build_path, 
            file_name, compiling_now_list, compiled_list, files_count, bll_version, failed_files))
            
    done, not_done = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)
    for future in concurrent.futures.as_completed(done):
        try:
            future.result()
        except Exception as exc:
            log(f'Thread generated an exception: {exc}')

    log(f"\tCOMPILED {len(compiled_list)} of {len(files)} (for {datetime.timedelta(seconds = time.time()-begin_time)} minutes)")
    if len(failed_files):
        log(f"\tFAILED FILES({len(failed_files)}): {failed_files}")
    return True


# -------------------------------------------------------------------------------------------------
def __extract_build__(build_path):
    build_zip_file = split_filename(build_path)
    if '.zip' in build_zip_file.lower():
        build_tmp_dir = os.path.join(tempfile.gettempdir(), build_zip_file)
        clean(build_tmp_dir)
        log(f'EXTRACTING BUILD "{build_path}" in "{build_tmp_dir}"')
        try:
            with zipfile.ZipFile(build_path) as z:
                z.extractall(os.path.join(tempfile.gettempdir(), build_zip_file))
                # запомним путь во временный каталог в качестве
                # нового пути к билду для последующего применения
                build_path = build_tmp_dir
        except BaseException as exc:
            log(f'\tERROR EXTRACTING BUILD "{exc}"')
        # конец разархивации
    return build_path


# -------------------------------------------------------------------------------------------------
def is_20_version(version):
    return ('20.1' in version) or ('20.2' in version) or ('20.3' in version)


# -------------------------------------------------------------------------------------------------
def __copy_build_ex__(build_path, build_path_crypto, destination_path, only_get_version):
    # проверка наличия пути build_path
    if not build_path:
        return
    if not os.path.exists(build_path):
        log(f'\tPATH {build_path} does not exists')
        return
    # если ссылка на билд указывает не на каталог, а на файл архива
    # попробуем провести разархивацию во временный каталог
    build_path = __extract_build__(build_path)
    if build_path_crypto:
        build_path_crypto = __extract_build__(build_path_crypto)
    # определяем версию билда
    version = extract_build_version(build_path)
    if not only_get_version:
        if is_20_version(version):
            for release in ['32', '64']:
                win_rel = f'Win{release}\\Release'
                src = os.path.join(build_path, win_rel)
                dst = os.path.join(destination_path, win_rel)
                clean(dst)
                log(f'COPYING BUILD {version} from "{src}" to "{dst}"')
                copy_files_from_all_subdirectories(src, dst, ['*.exe', '*.ex', '*.bpl', '*.dll'])
                if build_path_crypto:
                    src = os.path.join(build_path_crypto, win_rel)
                    log(f'COPYING CRYPTO BUILD {version} from "{src}" to "{dst}"')
                    copy_files_from_all_subdirectories(src, dst, ['CryptLib.dll', 'cr_*.dll'])
        else:
            clean(destination_path)
            log(f'COPYING BUILD {version} from "{build_path}" to "{destination_path}"')
            copy_files_from_all_subdirectories(build_path, destination_path, ['*.exe', '*.ex', '*.bpl', '*.dll'])
            if build_path_crypto:
                log(f'COPYING CRYPTO BUILD {version} from "{build_path}" to "{destination_path}"')
                copy_files_from_all_subdirectories(build_path_crypto, destination_path, ['CryptLib.dll', 'cr_*.dll'])
    return version


# -------------------------------------------------------------------------------------------------
def __copy_build__(build_path, build_path_crypto, destination_path):
    return __copy_build_ex__(build_path, build_path_crypto, destination_path, False)


# -------------------------------------------------------------------------------------------------
def get_build_version(settings):
    log('Detecting BUILD VERSION')
    version = __copy_build_ex__(settings.BuildBK, None, None, True)
    log(f'\tBUILD VERSION is {version}')
    return version


# -------------------------------------------------------------------------------------------------
def download_build(settings):
    build = settings.BuildBK
    build_ic = settings.BuildIC
    build_crypto = settings.BuildCrypto
    build_version = build_ic_version = ''
    instances = []
    if build:
        instances.append(INSTANCE_BANK)
        instances.append(INSTANCE_CLIENT)
        instances.append(INSTANCE_CLIENT_MBA)
        build_version = __copy_build__(build, build_crypto, DIR_BUILD_BK)
    if build_ic and settings.PlaceBuildIntoPatchIC:
        instances.append(INSTANCE_IC)
        build_ic_version = __copy_build__(build_ic, build_crypto, DIR_BUILD_IC)

    if not len(instances):
        return False

    for instance in instances:
        if instance in [INSTANCE_BANK, INSTANCE_CLIENT, INSTANCE_CLIENT_MBA]:
            is20 = is_20_version(build_version)
            # это копируются все файлы, которые будут участвовать в компиляции BLS на следующем шаге
            # т.к. в результате __copy_build__ весь билд оказывается разделен на Win32 и Win64
            if is20 and instance == INSTANCE_BANK:
                build_path = os.path.join(DIR_BUILD_BK, 'Win32\\Release')
                copy_files_from_all_subdirectories(build_path, DIR_BUILD_BK, ['*.*'])
            if instance == INSTANCE_BANK:
                for filepath in settings.BuildAdditionalFolders:
                    log(f'COPYING ADDITIONAL from "{filepath}" to "{DIR_BUILD_BK}"')
                    copy_files_from_all_subdirectories(filepath, DIR_BUILD_BK, ['*.*'])
        else:
            is20 = is_20_version(build_ic_version)
        settings.Is20Version = is20

        #  Если в настройках включено копирование билда в патч
        if settings.PlaceBuildIntoPatchBK:  # or settings.PlaceBuildIntoPatchIC
            log(f'COPYING build into patch for {instance}')
            excluded_files = ''
            if instance == INSTANCE_BANK:
                excluded_files = EXCLUDED_BUILD_FOR_BANK
            elif instance == INSTANCE_IC:
                excluded_files = EXCLUDED_BUILD_FOR_BANK
            elif instance in [INSTANCE_CLIENT, INSTANCE_CLIENT_MBA]:
                excluded_files = const_excluded_build_for_CLIENT

            mask_for_exe_dir = ['*.exe', '*.ex', '*.bpl', 'LocProt.dll', 'PerfControl.dll']
            excluded_for_system_dir = excluded_files + ['LocProt.dll', 'PerfControl.dll']
            excluded_for_system_client_dir = const_excluded_build_for_CLIENT + ['LocProt.dll', 'PerfControl.dll']

            if is20:  # для билда 20-ой версии
                if instance == INSTANCE_IC and settings.PlaceBuildIntoPatchIC:  # выкладываем билд плагина для ИК
                    mask = ['BssPluginSetup.exe', 'BssPluginSetupAdmin.exe', 'BssPluginSetupNoHost.exe',
                            'BssPluginWebKitSetup.exe', 'BssPluginSetup64.exe', 'BssPluginSetupGPB.exe',
                            'BssPluginSetupGPBNoHost.exe']
                    for release in ['32', '64']:  # выкладываем билд в LIBFILES32(64).BNK
                        build_path = os.path.join(DIR_BUILD_IC, 'Win{}\\Release'.format('32'))
                        for www_path in [dir_patch_libfiles_bnk_www_bsisites_rtic_code_buildversion(build_ic_version,release),
                                        dir_patch_libfiles_bnk_www_bsisites_rtwa_code_buildversion(build_ic_version,release)]:
                            copy_files_from_all_subdirectories(build_path, www_path, mask)

                elif instance != INSTANCE_IC and settings.PlaceBuildIntoPatchBK:
                    if instance == INSTANCE_BANK:
                        build_path = os.path.join(DIR_BUILD_BK, 'Win32\\Release')
                        # это копируются все файлы, которые будут участвовать в компиляции BLS на следующем шаге
                        # т.к. в результате __copy_build__ весь билд оказывается разделен на Win32 и Win64
                        copy_files_from_all_subdirectories(build_path, DIR_BUILD_BK, ['*.*'])
                        # copy_files_from_all_subdirectories(build_path, dir_patch(), ['CBStart.exe'])  # один файл CBStart.exe в корень патча
                        mask = ['bssetup.msi', 'CalcCRC.exe']
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_inettemp(), mask)
                        mask = ['BssPluginSetup.exe', 'BssPluginWebKitSetup.exe']
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_inettemp(), mask)
                    for release in ['32', '64']:  # выкладываем остальной билд для Б и БК для версий 32 и 64
                        build_path = os.path.join(DIR_BUILD_BK, f'Win{release}\\Release')
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_exe(instance, release), mask_for_exe_dir, excluded_files)
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_system(instance, release), ['*.dll'], excluded_for_system_dir)
                        copy_files_from_all_subdirectories(build_path, dir_patch_cbstart(instance, release), ['CBStart.exe'])
                        if instance == INSTANCE_BANK:
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk(release), ['UpdateIc.exe'])
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_www_exe(release), ['bsiset.exe'])
                            mask = ['bsi.dll', 'bsi.jar']
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_www_bsiscripts_rtic(release), mask)
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_www_bsiscripts_rtwa(release), mask)
                            # заполняем TEMPLATE шаблон клиента в банковском патче
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distribx_client_exe(release), mask_for_exe_dir, const_excluded_build_for_CLIENT)
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distribx_client_system( release), ['*.dll'], excluded_for_system_client_dir)
                            mask = ['CalcCRC.exe', 'Setup.exe', 'Install.exe', 'eif2base.exe', 'ilKern.dll', 'GetIName.dll']
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distribx(release), mask)
                            mask = ['ilGroup.dll', 'iliGroup.dll', 'ilProt.dll', 'ilCpyDoc.dll']
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_languagex_en(release), mask)
                            copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_languagex_ru(release), mask)

            else:  # для билдов 15 и 17
                build_path = DIR_BUILD_BK
                if instance in [INSTANCE_BANK, INSTANCE_CLIENT, INSTANCE_CLIENT_MBA] \
                        and settings.PlaceBuildIntoPatchBK:
                    # выкладываем билд для Б и БК
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_exe(instance), mask_for_exe_dir, excluded_files)
                    if settings.ClientEverythingInEXE and instance == INSTANCE_CLIENT:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_exe(instance), ['*.dll'], excluded_for_system_dir)
                    else:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_system(instance), ['*.dll'], excluded_for_system_dir)

                if instance == INSTANCE_BANK and settings.PlaceBuildIntoPatchBK:
                    copy_files_from_all_subdirectories(build_path, dir_patch(), ['CBStart.exe'])  # один файл в корень
                    # заполняем билдом TEMPLATE шаблон клиента в банковском патче
                    mask = ['*.exe', '*.ex', '*.bpl']
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distrib_client_exe(), mask, const_excluded_build_for_CLIENT)
                    if settings.ClientEverythingInEXE:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distrib_client_exe(), ['*.dll'], excluded_for_system_client_dir)
                    else:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distrib_client_system(), ['*.dll'], excluded_for_system_client_dir)
                    mask = ['CalcCRC.exe', 'Setup.exe', 'Install.exe', 'eif2base.exe', 'ilKern.dll', 'GetIName.dll']
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_distrib(), mask)
                    mask = ['ilGroup.dll', 'iliGroup.dll', 'ilProt.dll', 'ilCpyDoc.dll']
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_language_en(), mask)
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_language_ru(), mask)
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_language_en_client_system(), mask)
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_template_language_ru_client_system(), mask)
                    # заполняем LIBFILES.BNK в банковском патче билдом для БК
                    mask = ['autoupgr.exe', 'bscc.exe', 'compiler.exe', 'operedit.exe', 'testconn.exe', 'treeedit.exe']
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_add(), mask)
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_bsiset_exe(), ['bsiset.exe'])
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_license_exe(), ['protcore.exe'])

                if instance == INSTANCE_IC and settings.PlaceBuildIntoPatchIC:
                    # заполняем LIBFILES.BNK в банковском патче билдом для ИК
                    build_path = DIR_BUILD_IC
                    mask = ['bssaxset.exe', 'inetcfg.exe', 'rts.exe', 'rtsconst.exe', 'rtsinfo.exe']
                    if settings.BuildRTSZIP:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_rts_exe(), mask)
                    else:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_exe(INSTANCE_BANK), mask)
                    mask = ['llComDat.dll', 'llrtscfg.dll', 'llxmlman.dll', 'msxml2.bpl']
                    if settings.BuildRTSZIP:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_rts_system(), mask)
                    else:
                        copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_system(INSTANCE_BANK), mask)
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_www_bsiscripts_rtic(), ['bsi.dll'])
                    copy_files_from_all_subdirectories(build_path, dir_patch_libfiles_bnk_www_bsiscripts_rtadmin(), ['bsi.dll'])
                    # todo INETTEMP
    return True


# -------------------------------------------------------------------------------------------------
def copy_bls(clean_destination_dir, source_dir, destination_dir):
    bls_version = '15'
    if os.path.exists(source_dir):
        # source_dir = const_dir_COMPARED_BLS
        # dest_dir = dir_PATCH_LIBFILES_SOURCE
        if os.path.exists(os.path.join(source_dir, 'SOURCE')):
            # если такой путь существует, значит BLS выложены как для 17/20 версии
            source_dir = os.path.join(source_dir, 'SOURCE')
            destination_dir = os.path.join(destination_dir, 'BLS')
            bls_version = '17/20'
        if clean_destination_dir:
            clean(destination_dir)
        log(f'COPYING BLS ("{bls_version}" version style) from "{source_dir}" to {destination_dir}')
        try:
            copy_tree(source_dir, destination_dir)
        except BaseException as exc:
            log(f'\tERROR when copying ({exc})')
            return False
        return True
    else:
        log(f'NOT COPYING BLS. Path {source_dir} not exists')
        return False


# -------------------------------------------------------------------------------------------------
def copy_bll(settings):
    log('COPYING BLL files to patch')
    bll_files_only_bank = list_files_remove_paths_and_change_extension(DIR_COMPARED_BLS, '.bll', ['?b*.bls'])
    bll_files_only_rts = list_files_remove_paths_and_change_extension(DIR_COMPARED_BLS, '.bll', ['RT_*.bls', 'sscommon.bls', 'ssxml.bls', 'sserrors.bls'])
    bll_files_only_mba = list_files_remove_paths_and_change_extension(DIR_COMPARED_BLS_SOURCE_RCK, '.bll', ['*.bls'])
    bll_files_all = list_files_remove_paths_and_change_extension(DIR_COMPARED_BLS, '.bll', ['*.bls'])
    bll_files_tmp = list_files_by_list(DIR_BUILD_BK, bll_files_all)
    if len(bll_files_tmp) != len(bll_files_all):
        log(f'\tERROR: Not all changed BLS files were compiled {list(set(bll_files_all) - set(bll_files_tmp))}')
        return False

    bll_files_client_mba = list(set(bll_files_all) - set(bll_files_only_bank) - set(bll_files_only_rts))
    bll_files_client = list(set(bll_files_client_mba) - set(bll_files_only_mba))
    bll_files_all = list(set(bll_files_all) - set(bll_files_only_rts))

    # копируем bll для банка по списку bll_files_all
    copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_user(INSTANCE_BANK), bll_files_all)
    # копируем bll для RTS по списку bll_files_only_rts
    if settings.BuildRTSZIP:
        if settings.Is20Version:
            for release in ['32', '64']:
                copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_bnk_rts_user(release), bll_files_only_rts)
        else:
            copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_bnk_rts_user(), bll_files_only_rts)
    else:
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_user(INSTANCE_BANK), bll_files_only_rts)

    # копируем bll для клиента по разнице списков  bll_files_all-bll_files_only_bank
    if settings.ClientEverythingInEXE:
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_exe(INSTANCE_CLIENT), bll_files_client)
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_exe(INSTANCE_CLIENT_MBA), bll_files_client_mba)
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_template_distrib_client_exe(), bll_files_client)
    else:
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_user(INSTANCE_CLIENT), bll_files_client)
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_user(INSTANCE_CLIENT_MBA), bll_files_client_mba)
        copy_files_from_all_subdirectories(DIR_BUILD_BK, dir_patch_libfiles_template_distrib_client_user(), bll_files_client)
    return True


# -------------------------------------------------------------------------------------------------
def copy_yaml():
    source_dir = DIR_COMPARED_WWW_RT_IC
    if os.path.exists(source_dir):
        yaml_list = list_files_of_directory(source_dir, "*.yaml")
        if len(yaml_list):
            destination_dir = dir_patch_libfilesreact()
            log(f'COPYING YAML files to {destination_dir}')
            copy_files_from_dir(source_dir, destination_dir, '*.yaml')
        else:
            log(f'NOT COPYING YAML. No yaml files in {source_dir}')
    else:
        log(f'NOT COPYING YAML. Path {source_dir} not exists')


# -------------------------------------------------------------------------------------------------
def copy_xsd():
    source_dir = DIR_COMPARED_XSD
    if os.path.exists(source_dir):
        destination_dir = dir_patch_libfiles_subsys_xsd(INSTANCE_BANK)
        log(f'COPYING XSD files to {destination_dir}')
        copy_tree(source_dir, destination_dir)
    else:
        log(f'NOT COPYING XSD. Path {source_dir} not exists')


# -------------------------------------------------------------------------------------------------
def copy_www(settings):
    source_dir = DIR_COMPARED_WWW
    if os.path.exists(source_dir):
        try:
            if settings.Is20Version:
                for release in ['32', '64']:
                    destination_dir = dir_patch_libfiles_bnk_www(release)
                    log(f'COPYING WWW files to {destination_dir}')
                    copy_tree(source_dir, destination_dir)
            else:
                destination_dir = dir_patch_libfiles_bnk_www()
                log(f'COPYING WWW files to {destination_dir}')
                copy_tree(source_dir, destination_dir)
        except BaseException as exc:
            log(f'\tERROR when copying ({exc})')
    else:
        log(f'NOT COPYING WWW. Path {source_dir} not exists')


# -------------------------------------------------------------------------------------------------
def copy_rt_tpl(settings):
    source_dir = DIR_COMPARED_RT_TPL
    if os.path.exists(source_dir):
        try:
            if settings.BuildRTSZIP:
                if settings.Is20Version:
                    for release in ['32', '64']:
                        destination_dir = dir_patch_libfiles_bnk_rts_subsys_template(release)
                        log(f'COPYING RT_TPL files to {destination_dir}')
                        copy_tree(source_dir, destination_dir)
                else:
                    destination_dir = dir_patch_libfiles_bnk_rts_subsys_template()
                    log(f'COPYING RT_TPL files to {destination_dir}')
                    copy_tree(source_dir, destination_dir)
            else:
                destination_dir = dir_patch_libfiles_subsys_template()
                log(f'COPYING RT_TPL files to {destination_dir}')
                copy_tree(source_dir, destination_dir)

        except BaseException as exc:
            log(f'\tERROR when copying ({exc})')
    else:
        log(f'NOT COPYING RT_TPL. Path {source_dir} not exists')


# -------------------------------------------------------------------------------------------------
def copy_CommonLibraries():
    source_dir = DIR_COMPARED_CommonLibraries
    if os.path.exists(source_dir):
        destination_dir = dir_patch_libfiles(INSTANCE_BANK)
        log(f'COPYING CommonLibraries files to {destination_dir}')
        copy_tree(source_dir, destination_dir)
    else:
        log(f'NOT COPYING CommonLibraries. Path {source_dir} not exists')


# -------------------------------------------------------------------------------------------------
def copy_rtf(settings):
    source_dirs = [DIR_COMPARED_RTF, DIR_COMPARED_RTF_BANK,
                DIR_COMPARED_RTF_CLIENT, DIR_COMPARED_RTF_REPJET]
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            destination_dirs = []
            what = 'RTF'
            # Общие и банковские
            if source_dir in [DIR_COMPARED_RTF, DIR_COMPARED_RTF_BANK]:
                destination_dirs.append(dir_patch_libfiles_subsys_print_rtf(INSTANCE_BANK))
            # Общие и клиентские
            if source_dir in [DIR_COMPARED_RTF, DIR_COMPARED_RTF_CLIENT]:
                destination_dirs.append(dir_patch_libfiles_subsys_print_rtf(INSTANCE_CLIENT))
                destination_dirs.append(dir_patch_libfiles_subsys_print_rtf(INSTANCE_CLIENT_MBA))
                destination_dirs.append(dir_patch_libfiles_template_distrib_client_subsys_print_rtf())
                if settings.BuildRTSZIP:
                    if settings.Is20Version:
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_rtf('32'))
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_rtf('64'))
                    else:
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_rtf())
            # RepJet для всех
            if source_dir == DIR_COMPARED_RTF_REPJET:
                what = 'RepJet'
                destination_dirs.append(dir_patch_libfiles_subsys_print_repjet(INSTANCE_BANK))
                destination_dirs.append(dir_patch_libfiles_subsys_print_repjet(INSTANCE_CLIENT))
                destination_dirs.append(dir_patch_libfiles_subsys_print_repjet(INSTANCE_CLIENT_MBA))
                destination_dirs.append(dir_patch_libfiles_template_distrib_client_subsys_print_repjet())
                if settings.BuildRTSZIP:
                    if settings.Is20Version:
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_repjet('32'))
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_repjet('64'))
                    else:
                        destination_dirs.append(dir_patch_libfiles_bnk_rts_subsys_instclnt_template_distrib_client_subsys_print_repjet())
            for destination_dir in destination_dirs:
                log(f'COPYING {what} files from {source_dir} to {destination_dir}')
                copy_files_from_dir(source_dir, destination_dir)
        else:
            log(f'NOT COPYING RTF from {source_dir}. Path not exists')


# -------------------------------------------------------------------------------------------------
def copy_mba_dll():
    copy_files_of_version(os.path.join(DIR_BUILD_BK, 'DLL'), DIR_BUILD_BK, 'Win32', ['*.dll'], [])


# -------------------------------------------------------------------------------------------------
def make_decision_compilation_or_restart():
    continue_compilation = False
    if os.path.exists(DIR_AFTER_BLS):
        log(f'Folder {DIR_AFTER_BLS} EXISTS. So we could CONTINUE bls-compilation.\n\tAsking Maestro for decision.')
        continue_compilation = input('Maestro, please, ENTER any letter to CONTINUE bls compilation (otherwise patch building will be RESTARTED):') != ''
        if continue_compilation:
            log('\tMaestro decided to CONTINUE with bls-compilation instead of restart patch building')
        else:
            log('\tMaestro decided to RESTART patch building instead of CONTINUE with bls-compilation')
        if not continue_compilation:
            response = input(
                '\tREALLY?!\n\tMaestro, please, ENTER "Y" to CLEAR ALL and RESTART patch building:').upper()
            if response and response != 'Y':
                log(f'\tERROR: wrong answer {response}')
                exit(1000)
            continue_compilation = response != 'Y'
    return continue_compilation


# -------------------------------------------------------------------------------------------------
def get_git_log(settings):
    from_tag = settings.TagBefore
    to_tag = settings.TagAfter
    git_repo = Repo.init(DIR_AFTER)
    git = git_repo.git
    log_items = git.log('--format=%B', '--no-merges', '--abbrev-commit', f'{from_tag}..{to_tag}').split('\n')
    jira_tickets = []
    for log_item in log_items:
        found = re.findall(r'/?\w+-\d+', log_item)
        for jira_ticket in found:
            jira_tickets.append(jira_ticket.replace('/',''))
    if jira_tickets:
        file_name = get_filename_jira_tickets()
        make_dirs(os.path.dirname(file_name))
        with open(file_name, mode='w') as f:
            log(f'JIRA TICKETS from "{from_tag}" to "{to_tag}" saved to {file_name}')
            jira_tickets = list(dict.fromkeys(jira_tickets))  # removing duplicates
            f.writelines(','.join(jira_tickets))


# -------------------------------------------------------------------------------------------------
def patch():
    begin_time = time.time()
    log('=' * 120)
    global_settings = GlobalSettings()
    if not global_settings.was_success():
        log('SETTINGS FAILED')
        return

    continue_compilation = make_decision_compilation_or_restart()
    if not continue_compilation:
        if not clean(DIR_TEMP):
            log('CLEAN FAILED')
            return

    # Если пользователь не выбрал продолжение компиляции, запустим
    # ЭТАП ЗАГРУЗКИ ПО МЕТКАМ И СРАВНЕНИЯ РЕВИЗИЙ:
    if not continue_compilation:
        log('PATCH PREPARATION BEGIN')
        if not download_from_git(global_settings):
            log('DOWNLOAD FAILED')
            return
        get_git_log(global_settings)  # формирование списка тикетов

        if not compare_directories_before_and_after():
            log('EXIT')
            return

        copy_yaml()
        copy_xsd()
        copy_rt_tpl(global_settings)
        copy_rtf(global_settings)
        copy_CommonLibraries()

        for instance in [INSTANCE_BANK, INSTANCE_CLIENT, INSTANCE_CLIENT_MBA]:
            copy_table_10_files_for_data_files(instance)
            upgrade10_eif(instance)
        continue_compilation = copy_bls(True, DIR_COMPARED_BLS, dir_patch_libfiles_source())
        need_download_build = continue_compilation or global_settings.PlaceBuildIntoPatchBK or global_settings.PlaceBuildIntoPatchIC
        build_downloaded = False
        # если требуется загрузка билда (для компиляции или для помещения в патч)
        if need_download_build:
            build_downloaded = download_build(global_settings)
            #  если требуется загрузка билда и предыдущая загрузка основного билда успешна
            if build_downloaded:
                copy_mba_dll()

        # Если билд не скачивался (при этом мы определяемся с версией билда),
        # то все равно попробуем получить его версию, чтобы определиться с каталогами
        # для выкладывания ИК
        if not build_downloaded:
            build_version = get_build_version(global_settings)
            global_settings.Is20Version = is_20_version(build_version)
        continue_compilation = continue_compilation and (build_downloaded or not need_download_build)

        # после определения версии билда, потому что надо знать версию билда, чтобы выкладывать WWW
        copy_www(global_settings)

    # если ЭТАП ЗАГРУЗКИ завершился успешно,
    # или пользователь выбрал переход к компиляции
    # запускаем ЭТАП КОМПИЛЯЦИИ bls-файлов:
    if continue_compilation:
        # запустим компиляцию этой каши
        if compile_all(global_settings.LicenseServer,
                    global_settings.LicenseProfile,
                    DIR_BUILD_BK, DIR_AFTER_BLS,
                    global_settings.BLLVersion):
            # копируем готовые BLL в патч
            copy_bll(global_settings)
    log(f'DONE (for {datetime.timedelta(seconds = time.time()-begin_time)} minutes)')


def compile_only():
    # пока не реализовано ----------------------------------------------
    log('=' * 120)
    global_settings = GlobalSettings()  # read_config()
    if not global_settings.was_success():
        return
    if not clean(DIR_TEMP):
        return
    if download_build(global_settings):
        if download_from_git(global_settings):
            compile_all(global_settings.LicenseServer, global_settings.LicenseProfile,
                        DIR_BUILD_BK, DIR_AFTER_BLS, global_settings.BLLVersion)


if __name__ == "__main__":
    argument = None
    if len(sys.argv) > 1:
        argument = sys.argv[1]
    if not argument or argument == '/patch' or argument == '-patch':
        patch()
    elif argument == '/compile' or argument == '-compile':
        compile_only()
    else:
        log(f'UNKNOWN ARGUMENT {argument}')