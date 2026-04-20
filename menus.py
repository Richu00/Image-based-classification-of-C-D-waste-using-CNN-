"""
menus.py
--------
All sub-menu loop functions for the music player UI.

Every function in this module is a pure routing layer: it prints a
menu, reads a choice, and dispatches to the appropriate function in
``playlists``, ``library``, or ``favorites``. No business logic lives
here.

Functions
---------
playlist_menu()
    Menu for creating, switching, renaming, viewing, and deleting playlists.
edit_playlist_menu()
    Menu for viewing, adding, deleting, and clearing songs in the active playlist.
playback_menu()
    Menu for play, pause, skip, volume, repeat, shuffle, and progress.
library_menu()
    Menu for searching or sorting the master library.
favorites_menu()
    Menu for adding the current song to favorites or viewing the list.
"""

import playlists as pl
from library   import search_song, sort_master_library, master_library
from favorites import add_to_favorites, show_favorites


# ──────────────────────────────────────────────────────────────────────────────
# Playlist menu
# ──────────────────────────────────────────────────────────────────────────────

def playlist_menu() -> None:
    """
    Display the Playlist Options menu and route user input.

    Options
    -------
    1  Create a new empty playlist.
    2  Create a random playlist from the master library.
    3  Switch to an existing playlist.
    4  List all playlists.
    5  Delete a playlist.
    6  Rename a playlist.
    0  Return to the main menu.
    """
    while True:
        print("""
--- PLAYLIST OPTIONS ---

1. Create Playlist
2. Create Random Playlist
3. Switch Playlist
4. Show All Playlists
5. Delete Playlist
6. Rename Playlist
0. Back
""")
        choice = input("Choose option: ")

        if   choice == "1": pl.create_new_playlist()
        elif choice == "2": pl.create_random_playlist()
        elif choice == "3": pl.switch_playlist()
        elif choice == "4": pl.show_all_playlists()
        elif choice == "5": pl.delete_playlist()
        elif choice == "6": pl.rename_playlist()
        elif choice == "0": break
        else:               print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Edit playlist menu
# ──────────────────────────────────────────────────────────────────────────────

def edit_playlist_menu() -> None:
    """
    Display the Edit Playlist menu and route user input.

    Guards against execution when no playlist is active and exits
    early with a notice if that is the case.

    Options
    -------
    1  View all songs in the current playlist.
    2  Add a song chosen from the master library.
    3  Delete a song by its position number.
    4  Clear the entire playlist.
    0  Return to the main menu.
    """
    if not pl.current_playlist:
        print("No playlist selected.")
        return

    while True:
        print(f"""
--- EDIT PLAYLIST ({pl.current_playlist.name}) ---

1. View Songs
2. Add Song from Library
3. Delete Song
4. Clear Playlist
0. Back
""")
        choice = input("Choose option: ")

        if choice == "1":
            pl.current_playlist.show_playlist()

        elif choice == "2":
            # Print the full library so the user can choose by number
            print("\nMaster Library:")
            for i, song in enumerate(master_library, 1):
                print(f"  {i}. {song}")
            try:
                num = int(input("Select song number: "))
                pl.current_playlist.add_song(master_library[num - 1])
            except (ValueError, IndexError):
                print("Invalid selection.")

        elif choice == "3":
            pl.current_playlist.show_playlist()
            try:
                pos = int(input("Enter song number to delete: "))
                pl.current_playlist.delete_song(pos)
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "4":
            pl.current_playlist.clear()

        elif choice == "0":
            break

        else:
            print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Playback menu
# ──────────────────────────────────────────────────────────────────────────────

def playback_menu() -> None:
    """
    Display the Playback Controls menu and route user input.

    Guards against execution when no playlist is active and exits
    early with a notice if that is the case.

    Options
    -------
    1  Play the current song (fresh start, resets elapsed time).
    2  Resume from where the song was paused (keeps elapsed time).
    3  Skip to the next song (respects shuffle and repeat settings).
    4  Go back to the previous song.
    5  Pause playback.
    6  Set the volume (0–100).
    7  Toggle repeat mode on / off.
    8  Toggle shuffle mode on / off.
    9  Show elapsed playback time for the current song.
    0  Return to the main menu.
    """
    if not pl.current_playlist:
        print("No playlist selected.")
        return

    while True:
        # Check whether the current song has finished before rendering the menu.
        # This is the auto-advance hook — no threads needed.
        pl.current_playlist.check_and_advance()

        print(f"""
--- PLAYBACK MENU ({pl.current_playlist.name}) ---

1. Play
2. Resume
3. Next
4. Previous
5. Pause
6. Change Volume
7. Toggle Repeat
8. Toggle Shuffle
9. Show Progress
0. Back
""")
        choice = input("Choose option: ")

        if   choice == "1": pl.current_playlist.play()
        elif choice == "2": pl.current_playlist.resume()
        elif choice == "3": pl.current_playlist.next_song()
        elif choice == "4": pl.current_playlist.previous_song()
        elif choice == "5": pl.current_playlist.pause()
        elif choice == "7": pl.current_playlist.toggle_repeat()
        elif choice == "8": pl.current_playlist.toggle_shuffle()
        elif choice == "9": pl.current_playlist.show_progress()

        elif choice == "6":
            # Volume requires parsing — wrap in try/except for safety
            try:
                vol = int(input("Enter volume (0-100): "))
                pl.current_playlist.change_volume(vol)
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "0":
            break

        else:
            print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Library menu
# ──────────────────────────────────────────────────────────────────────────────

def library_menu() -> None:
    """
    Display the Library Options menu and route user input.

    Options
    -------
    1  Search the master library by title or artist.
    2  Sort the master library by title or artist.
    0  Return to the main menu.
    """
    while True:
        print("""
--- LIBRARY MENU ---

1. Search Song
2. Sort Master Library
0. Back
""")
        choice = input("Choose option: ")

        if   choice == "1": search_song(pl.current_playlist)
        elif choice == "2": sort_master_library()
        elif choice == "0": break
        else:               print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Favorites menu
# ──────────────────────────────────────────────────────────────────────────────

def favorites_menu() -> None:
    """
    Display the Favorites menu and route user input.

    Options
    -------
    1  Add the currently playing song to the favorites list.
    2  View all favorited songs.
    0  Return to the main menu.
    """
    while True:
        print("""
--- FAVORITES MENU ---

1. Add Current Song to Favorites
2. Show Favorites
0. Back
""")
        choice = input("Choose option: ")

        if   choice == "1": add_to_favorites(pl.current_playlist)
        elif choice == "2": show_favorites()
        elif choice == "0": break
        else:               print("Invalid choice.")
