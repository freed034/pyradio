import sys
import requests
import subprocess
from os.path import join, exists, isdir
from os import environ, makedirs, listdir, replace, remove, sep
from time import sleep
import site
from shutil import rmtree
from msvcrt import getwch
from msvcrt import getwch
from os import sep
import subprocess


HAVE_PYUNPACK = True
try:
    from pyunpack import Archive
except ModuleNotFoundError:
    HAVE_PYUNPACK = False

''' This is also to be able to execute it manually'''
try:
    from .player import find_mpv_on_windows, find_mplayer_on_windows, find_vlc_on_windows
except ImportError:
    from player import find_mpv_on_windows, find_mplayer_on_windows, find_vlc_on_windows

def win_press_any_key_to_unintall():
    the_path = __file__.split(sep)
    the_file = sep.join(the_path[:-1]) + sep + 'install.py'
    print('\nTo complete the process you will have to execute a batch file.')
    print('Windows Explorer will open the location of the batch file to run.')
    print('')
    print('Please double click')
    print('')
    print('    uninstall.bat')
    print('')
    print('to remove PyRadio from your system.')
    print('')
    print('After you are done, you can delete the folder it resides in.')
    from .win import press_any_key_to_continue
    print('\nPress any key to exit...', end='', flush=True)
    getwch()
    #print('\nPress any key to exit...', end='', flush=True)
    #getwch()
    subprocess.call('python ' + the_file + ' -R',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

def win_print_exe_paths():
    from .install import fix_pyradio_win_exe
    exe = fix_pyradio_win_exe()
    if exe[0] and exe[1]:
        print('PyRadio EXE files:')
        print('  System:\n    {}'.format(exe[0]))
        print('  User:\n    {}'.format(exe[1]))
    else:
        print('PyRadio EXE file:')
        if exe[0]:
            print('  {}'.format(exe[0]))
        else:
            print('  {}'.format(exe[1]))
    # doing it this way so that pyton2 does not break (#153)
    from .win import press_any_key_to_continue
    print('\nPress any key to exit...', end='', flush=True)
    getwch()

def press_any_key_to_continue():
    print('\nPress any key to exit...', end='', flush=True)
    from msvcrt import getwch
    getwch()

def install_module(a_module, do_not_exit=False, print_msg=True):
    if print_msg:
        print('Installing module: ' + a_module)
    for count in range(1,6):
        ret = subprocess.call('python -m pip install --upgrade ' + a_module,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        if ret == 0:
            break
        else:
            if count < 5:
                if print_msg:
                    print('  Download failed. Retrying {}/5'.format(count+1))
            else:
                if print_msg:
                    print('Failed to download module...\nPlease check your internet connection and try again...')
                else:
                    print('Failed to download module "{}"...\nPlease check your internet connection and try again...').format(a_module)
                if do_not_exit:
                    return False
                sys.exit(1)
        return True

def find_pyradio_win_exe():
    ''' find pyradio EXE files

        Return (system_exe, user_exe)
    '''
    exe = [None, None]
    for a_path in site.getsitepackages():
        an_exe = join(a_path, 'Scripts' , 'pyradio.exe')
        if exists(an_exe):
            exe[0] = an_exe
            break
    an_exe = join(site.getuserbase(), 'Scripts' , 'pyradio.exe')
    if exists(an_exe):
        exe[1] = an_exe
    # print(exe)
    return exe

def _is_player_in_path(a_player):
    ''' Return player's path in PATH variable
        If player not in PATH, return None
        Makes sure the path is local to user
        and player EXE exists

        Parameter:
            a_player: 1=mpv, 2=mplayer
    '''
    a_player -= 1
    in_path = None
    pl = ('mpv', 'mplayer')
    for a_path in environ['PATH'].split(';'):
        if a_path.endswith(pl[a_player]):
            in_path = a_path
            break
    #print('in_payh: {}'.format(in_path))
    if in_path:
        if not environ['USERPROFILE'] in a_path:
            return None
        if not exists(join(in_path, pl[a_player] + '.exe')):
            return None
    return in_path

def _get_output_folder(package, output_folder=None, do_not_exit=False):

    if output_folder is None:
        a_path = _is_player_in_path(package)
        if a_path:
            sp = a_path.split(sep)
            output_folder = sep.join(sp[:-1])
        else:
            output_folder = join(environ['APPDATA'], 'pyradio')
        # rename mpv if already there
        if not exists(output_folder):
            # create dir
            makedirs(output_folder, exist_ok=True)
            if not exists(output_folder):
                print('Failed to create folder: "{}"'.format(pyradio_dir))
                if do_not_exit:
                    return None
                sys.exit(1)
    return output_folder

def _get_out_file(output_folder):
    count = 0
    while True:
        out_file = join(output_folder, 'download-{}.7z'.format(count))
        if exists(out_file):
            count += 1
        else:
            break
    return join(output_folder, out_file)

def download_player(output_folder=None, package=1, do_not_exit=False):
    # Parameters
    #   output_folder   : where to save files
    #   package         : 0: mpv, 1: mplayer
    package -= 1
    if package == 0:
        print('Downloading MPV (latest)...')
    else:
        print('Downloading MPlayer (latest)...')
    url = ('https://sourceforge.net/projects/mpv-player-windows/files/latest/download',
        'https://sourceforge.net/projects/mplayer-win32/files/latest/download')

    output_folder = _get_output_folder(
        output_folder=output_folder,
        package=package,
        do_not_exit=do_not_exit)
    if output_folder is None:
        return False

    print('    into "{}"'.format(output_folder))

    out_file = _get_out_file(output_folder)

    session = requests.Session()
    for count in range(1,6):
        try:
            r = session.get(url[package])
            r.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if count < 5:
                print('  Download failed. Retrying {}/5'.format(count+1))
            else:
                print('Failed to download player...\nPlease check your internet connection and try again...')
                if do_not_exit:
                    return False
                sys.exit(1)
    print('  Saving: ' + out_file)
    try:
        with open(out_file, 'wb') as f:
            f.write(r.content)
    except:
        print('Failed to write archive...\nPlease try again later...')
        if do_not_exit:
            return False
        sys.exit(1)

    print('Extracting archive...')
    if not HAVE_PYUNPACK:
        for a_module in ('pyunpack', 'patool'):
            install_module(a_module, print_msg=False)
    from pyunpack import Archive

    patool_exec = join(site.USER_SITE.replace('site-packages', 'Scripts'), 'patool')
    if not exists(patool_exec):
        patool = None
    try:
        Archive(out_file).extractall(join(output_folder, 'mpv' if package==0 else ''),
            auto_create_dir=True,
            patool_path=patool_exec)
    except:
            print('Failed to extract the archive...\nPlease try again later...')
            if do_not_exit:
                return False
            sys.exit(1)

    if not _post_download(package, output_folder, do_not_exit):
        return False
    remove(out_file)
    return True


def _post_download(package, output_folder, do_not_exit):

    # rename MPlayer directory
    if package == 1:
        sleep(5)
        mplayer_dir_found = False
        extracted_dirname = None
        dir_list = listdir(output_folder)
        for a_file in dir_list:
            if a_file == 'mplayer':
                mplayer_dir_found = True
            elif a_file.startswith('MPlayer-') and \
                    isdir(join(output_folder, a_file)):
                extracted_dirname = a_file

        # rename extracted dir to mplayer
        if extracted_dirname:
            extracted_dirname = join(output_folder, extracted_dirname)
            mplayer_final_dir = join(output_folder, 'mplayer')
            mplayer_old_dir = join(output_folder, 'mplayer.old')

            if mplayer_dir_found:
                if exists(mplayer_old_dir):
                    try:
                        rmtree(mplayer_old_dir)
                    except OSError:
                        print('Failed to remove "{}"\nPlease close all programs and try again...'.format(mplayer_old_dir))
                        if do_not_exit:
                            return False
                        sys.exit(1)
                try:
                    replace(mplayer_final_dir, mplayer_old_dir)
                except:
                    print('Failed to rename folder "{0}"\n      to "{1}"...\nPlease close all open programs and try again...'.format(mplayer_final_dir, mplayer_old_dir))
                    if do_not_exit:
                        return False
                    sys.exit(1)
            try:
                replace(join(output_folder, extracted_dirname), join(output_folder, 'mplayer'))
            except:
                print('Failed to rename folder "{0}" to\n      "{1}"...\nPlease close all open programs and try again...'.format(extracted_dirname, mplayer_final_dir))
                if do_not_exit:
                    return False
                sys.exit(1)

        else:
            print('Extracted folder not found...\nPlease try again later...')
            if do_not_exit:
                return False
            sys.exit(1)
    return True

def install_player(output_folder=None, package=0, do_not_exit=False):
    while True:
        in_path = [None, None, None]
        to_do = ['1. Install', '2. Install', 'VLC media player is not installed']
        from_path = ['', '']
        for n in range(0, 2):
            in_path[n] = _is_player_in_path(n)
            if in_path[n]:
                to_do[n] = '{}. Update'.format(n+1)
                from_path[n] = ' (found in PATH)'
        if in_path[0] is None:
            in_path[0] = find_mpv_on_windows()
        if in_path[1] is None:
            in_path[1] = find_mplayer_on_windows()

        if in_path[0] == 'mpv':
            in_path[0] = None
        if in_path[1] == 'mplayer':
            in_path[1] = None

        for n in range(0, 2):
            if in_path[n]:
                to_do[n] = '{}. Update'.format(n+1)
        if find_vlc_on_windows():
            to_do[2] = 'VLC media player is already installed'
        #print(in_path)
        #print(to_do)
        #print(from_path)

        #print('\nDo you want to download a media player now? (Y/n): ', end='', flush=True)
        #x = getwch()
        #print(x)
        x = 'y'
        if in_path[0]:
            best_choise = ''
        else:
            best_choise = '(best choise)'
        if x == 'y' or x == '\n' or x == '\r':
            x = ''
            msg = '''
Please select an action:
    {0} MPV{1}      {2}
    {3} MPlayer{4}'''


            print(msg.format(to_do[0], from_path[0],
                best_choise, to_do[1], from_path[1]
            ))
            msg ='''
    Note:
      {}
    '''
            opts = []
            prompt = ''
            all_uninstall = False
            if in_path[0] is None and in_path[1] is None:
                opts = ['0', '1', '2', 'q']
                prompt = 'Press 1, 2 or q to Cancel: '
            elif in_path[0] is not None and in_path[1] is not None:
                print('\n    3. Uninstall MPV')
                print('    4. Uninstall MPlayer')
                opts = ['0', '1', '2', '3', '4', 'q']
                prompt = 'Press 1, 2, 3, 4 or q to Cancel: '
            else:
                if in_path[0] is not None:
                    print('\n    3. Uninstall MPV')
                else:
                    print('\n    3. Uninstall MPlayer')
                opts = ['0', '1', '2', '3', 'q']
                prompt = 'Press 1, 2, 3 or q to Cancel: '
                all_uninstall = True

            print(msg.format(to_do[2]))



            while x not in opts:
                print(prompt,  end='', flush=True)
                x = getwch()
                print(x)

            # ok, parse response
            if x in ('0', 'q'):
                clean_up()
                return
            if x in ('1', '2'):
                # install ot update
                download_player(package=int(x))
                print('\n\n')
            elif x == '3':
                # find out which player to wuninstall
                print('uninstall mplayer or mpv')
                print('\n\n')
            elif x == '4':
                # uninstall mplayer
                print('uninstall mplayer')
                print('\n\n')

def install_pylnk(a_path, do_not_exit=False):
    print('    Downloading pylnk...')
    session = requests.Session()
    for count in range(1,6):
        try:
            r = session.get('https://github.com/strayge/pylnk/archive/refs/heads/master.zip')
            r.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if count < 5:
                print('      Download failed. Retrying {}/5'.format(count+1))
            else:
                print('    Failed to download pylnk...\nPlease check your internet connection and try again...')
                if do_not_exit:
                    return False
                sys.exit(1)
    try:
        with open(join(a_path, 'pylnk.zip'), 'wb') as f:
            f.write(r.content)
    except:
        print('    Failed to write archive...\nPlease try again later...')
        if do_not_exit:
            return False
        sys.exit(1)

    print('    Installing pylnk...')
    ret = subprocess.call('python -m pip install ' + join(a_path, 'pylnk.zip'),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    remove(join(a_path, 'pylnk.zip'))

def clean_up(print_msg=True):
    if print_msg:
        print('Cleaning up makedepend modules...')
    for n in ('pyunpack', 'patool', 'pylnk3', 'EasyProcess'):
        subprocess.call('python -m pip uninstall -y ' + n,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

def create_pyradio_link():
    sp = site.USER_SITE.split(sep)
    sp[-1] = 'Scripts'
    scripts_path = sep.join(sp)
    pyradio_exe = join(scripts_path, 'pyradio.exe')
    pylnk_exe = join(scripts_path, 'pylnk3.exe')
    icon = join(environ['APPDATA'], 'pyradio', 'help', 'pyradio.ico')
    link_path = join(environ['APPDATA'], 'pyradio', 'help', 'PyRadio.lnk')
    workdir = join(environ['APPDATA'], 'pyradio')
    if exists(pyradio_exe):
        print('*** Updating Dekstop Shortcut')
        if not exists(workdir):
            makedirs(workdir, exist_ok=True)
            if not exists(workdir):
                print('Cannot create "' + workdir + '"')
                sys.exit(1)
        if not exists(pylnk_exe):
            install_pylnk(workdir)
        cmd = pylnk_exe + ' c --icon ' + icon + ' --workdir ' + workdir \
            + ' ' + pyradio_exe + ' ' + link_path
        #print(cmd)
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    # _post_download(1, "C:\\Users\\spiros\\AppData\\Roaming\\pyradio")
    # download_player(package=0)
    install_player()

    # install_pylnk("C:\\Users\\spiros")
    #create_pyradio_link()
    # find_pyradio_win_exe()