"""
Completed_Music_Player.py
--------------------------
A fully self-contained command-line music player.

Run with::

    python Completed_Music_Player.py

Classes
-------
Song
    Represents a single track (title + artist).
Node
    A single link in a doubly linked list, wrapping one Song.
MusicPlayer
    A named playlist backed by a doubly linked list with full playback
    controls, volume, repeat, shuffle, and elapsed-time tracking.

Global variables
----------------
master_library : list[Song]
    The full catalogue of songs available across all playlists.
favorites : list[Song]
    Songs the user has marked as favorites (shared across playlists).
playlists : dict[str, MusicPlayer]
    All created playlists, keyed by name.
current_playlist : MusicPlayer or None
    The currently active playlist. None until the user creates one.

Functions
---------
search_song()
    Search ``master_library`` by title or artist.
add_to_favorites()
    Add the currently playing song to ``favorites``.
show_favorites()
    Print every song in ``favorites``.
merge_sort(arr, key)
    Recursively sort a Song list using merge sort.
merge(left, right, key)
    Merge two sorted Song lists into one (internal helper).
sort_master_library()
    Interactively sort ``master_library`` in-place.
playlist_menu()
    Sub-menu for creating, switching, renaming, and deleting playlists.
create_new_playlist()
    Create a new empty playlist and make it active.
create_random_playlist()
    Create a playlist pre-filled with random songs and make it active.
switch_playlist()
    Change the active playlist.
show_all_playlists()
    List every playlist name.
rename_playlist()
    Rename an existing playlist, keeping all pointers in sync.
edit_playlist_menu()
    Sub-menu for viewing, adding, deleting, and clearing songs.
playback_menu()
    Sub-menu for play, pause, skip, volume, repeat, shuffle, progress.
favorites_menu()
    Sub-menu for favoriting songs or viewing the favorites list.
library_menu()
    Sub-menu for searching or sorting the master library.
menu()
    Main entry point — status header + top-level routing.
"""

import random
import time


# ──────────────────────────────────────────────────────────────────────────────
# Song
# ──────────────────────────────────────────────────────────────────────────────

class Song:
    """
    Represents a single music track.

    Attributes
    ----------
    title : str
        The title of the song.
    artist : str
        The name of the artist or artists.
    """

    def __init__(self, title: str, artist: str) -> None:
        self.title  = title
        self.artist = artist

    def __str__(self) -> str:
        """Return a human-readable ``'Title - Artist'`` string."""
        return f"{self.title} - {self.artist}"


# ──────────────────────────────────────────────────────────────────────────────
# Node
# ──────────────────────────────────────────────────────────────────────────────

class Node:
    """
    A single link in a doubly linked list.

    Each node wraps one Song and holds pointers to both neighbours,
    enabling O(1) forward and backward navigation through a playlist.

    Attributes
    ----------
    song : Song
        The track stored in this node.
    next : Node or None
        Pointer to the next node (None if this is the tail).
    prev : Node or None
        Pointer to the previous node (None if this is the head).
    """

    def __init__(self, song: Song) -> None:
        self.song = song
        self.next: "Node | None" = None
        self.prev: "Node | None" = None


# ──────────────────────────────────────────────────────────────────────────────
# MusicPlayer
# ──────────────────────────────────────────────────────────────────────────────

class MusicPlayer:
    """
    A named playlist backed by a doubly linked list.

    Supports adding and removing songs, sequential and shuffled playback,
    repeat mode, volume control, and real-time elapsed-time tracking.

    Attributes
    ----------
    name : str
        Display name of this playlist.
    head : Node or None
        First node in the linked list.
    tail : Node or None
        Last node in the linked list.
    current : Node or None
        The node that is currently selected or playing.
    is_playing : bool
        True while a song is actively playing.
    volume : int
        Playback volume in the range 0–100. Default is 50.
    repeat : bool
        When True, the playlist loops back to the head after the last song.
    shuffle : bool
        When True, ``next_song`` picks a random track instead of the next one.
    play_start_time : float or None
        ``time.time()`` stamp recorded when the current song started playing.
        Reset to None whenever playback is paused.
    elapsed_before_pause : float
        Accumulated seconds played before the most recent pause, so that
        progress survives pause/resume cycles correctly.
    """

    def __init__(self, name: str = "Default") -> None:
        self.name                            = name
        self.head:     "Node | None"         = None
        self.tail:     "Node | None"         = None
        self.current:  "Node | None"         = None
        self.is_playing:        bool         = False
        self.volume:            int          = 50
        self.repeat:            bool         = False
        self.shuffle:           bool         = False
        self.play_start_time:   "float|None" = None
        self.elapsed_before_pause: float     = 0.0

    # ── Adding / removing ─────────────────────────────────────────────────────

    def add_song(self, song: Song) -> None:
        """
        Append a song to the end of the playlist.

        If the playlist is empty the new node also becomes ``current`` so
        playback can begin immediately without a separate selection step.

        Parameters
        ----------
        song : Song
            The track to append.
        """
        new_node = Node(song)

        if not self.head:
            # Empty playlist — all three pointers point to the only node
            self.head = self.tail = new_node
            self.current = self.head
        else:
            # Non-empty — attach after the tail and advance the tail pointer
            self.tail.next = new_node
            new_node.prev  = self.tail
            self.tail      = new_node

        print(f"Added: {song}")

    def delete_song(self, position: int) -> None:
        """
        Remove the song at a 1-based position from the playlist.

        Relinks surrounding nodes and updates ``head``, ``tail``, and
        ``current`` so the list stays consistent after deletion.

        Parameters
        ----------
        position : int
            1-based index of the song to remove.
        """
        if not self.head:
            print("Playlist is empty")
            return

        # Walk forward until the node at the target index is reached
        temp  = self.head
        index = 1
        while temp and index < position:
            temp  = temp.next
            index += 1

        if not temp:
            print("Invalid position")
            return

        # Relink the previous neighbour, or promote the next node to head
        if temp.prev:
            temp.prev.next = temp.next
        else:
            self.head = temp.next

        # Relink the next neighbour, or retract the tail to the previous node
        if temp.next:
            temp.next.prev = temp.prev
        else:
            self.tail = temp.prev

        # If the deleted node was current, move to the nearest surviving node
        if self.current == temp:
            self.current = temp.next or temp.prev

        print(f"Deleted: {temp.song}")

    def clear(self) -> None:
        """Remove every song and reset all node pointers to None."""
        self.head = self.tail = self.current = None
        print("Playlist cleared")

    # ── Playback ──────────────────────────────────────────────────────────────

    # Simulated song duration in seconds.
    # Every song is treated as 3 minutes long. When total elapsed time
    # exceeds this value the player auto-advances to the next song.
    SONG_DURATION: int = 180

    def check_and_advance(self) -> None:
        """
        Check whether the current song has exceeded its simulated duration
        and auto-advance to the next song if it has.

        Called at the start of each playback menu loop iteration so that
        auto-advance is triggered the next time the user interacts with the
        menu, without requiring a background thread.

        Auto-advance only fires when:
        - A song is actively playing (not paused).
        - Total elapsed time has reached or exceeded ``SONG_DURATION``.

        Notes
        -----
        When repeat is ON, ``next_song()`` wraps back to the head of the
        playlist, so auto-advance still works — the playlist just loops.
        When the last song ends and repeat is OFF, ``next_song()`` prints
        "End of playlist" and stays put.
        """
        if not self.is_playing or not self.play_start_time:
            return   # paused or nothing playing — nothing to check

        # Total elapsed = banked time + live time since last play/resume
        total_elapsed = self.elapsed_before_pause + (time.time() - self.play_start_time)

        if total_elapsed >= self.SONG_DURATION:
            print(f"\n  ♪ '{self.current.song}' finished — auto-advancing...")
            self.next_song()   # respects shuffle and repeat settings

    def play(self) -> None:
        """
        Start playing the current song.

        Records ``play_start_time`` as the reference point for elapsed-time
        calculations and resets ``elapsed_before_pause`` because this is a
        fresh play of a new song.
        """
        if not self.current:
            print("Playlist is empty")
            return

        self.is_playing           = True
        self.play_start_time      = time.time()  # anchor point for elapsed time
        self.elapsed_before_pause = 0.0          # new song — reset accumulated time
        print(f"Currently playing: {self.current.song}")

    def pause(self) -> None:
        """
        Pause playback and bank the elapsed time.

        Adds the seconds played since the last resume to
        ``elapsed_before_pause`` so ``show_progress`` stays accurate
        after the track is resumed.
        """
        if self.is_playing and self.play_start_time:
            # Bank seconds played since the last resume before clearing the timer
            self.elapsed_before_pause += time.time() - self.play_start_time
            self.play_start_time = None

        self.is_playing = False
        print("Paused")

    def resume(self) -> None:
        """
        Resume playback of the current song from where it was paused.

        Unlike ``play()``, which resets ``elapsed_before_pause`` to zero
        and treats the song as freshly started, ``resume()`` picks up the
        accumulated time exactly where ``pause()`` left off.

        Does nothing if the song is already playing or no song is selected.
        """
        if not self.current:
            print("No song selected.")
            return

        if self.is_playing:
            print(f"Already playing: {self.current.song}")
            return

        # Keep elapsed_before_pause intact — just restart the timer from now
        self.is_playing      = True
        self.play_start_time = time.time()
        print(f"Resumed: {self.current.song}")

    def next_song(self) -> None:
        """
        Advance to the next song according to the active mode.

        Logic
        -----
        1. Shuffle ON  → delegate to ``_play_random_song``.
        2. More songs remain → move one step forward in the list.
        3. End of list + Repeat ON → wrap back to the head.
        4. End of list + Repeat OFF → notify and stay put.
        """
        if self.shuffle:
            self._play_random_song()
        elif self.current and self.current.next:
            self.current = self.current.next
            self.play()
        elif self.repeat:
            self.current = self.head   # loop back to the beginning
            self.play()
        else:
            print("End of playlist")

    def previous_song(self) -> None:
        """
        Go back to the previous song.

        Does nothing and prints a notice if the current song is already
        the first track in the list.
        """
        if self.current and self.current.prev:
            self.current = self.current.prev
            self.play()
        else:
            print("No previous song")

    def _play_random_song(self) -> None:
        """
        Pick and play a random song, excluding the current one.

        Traverses the list to collect all nodes, removes the current node
        from the candidate pool, then calls ``random.choice``. If the
        playlist has only one song that song is simply replayed.

        Notes
        -----
        This is a private helper method. External code should call
        ``next_song``, which routes here when shuffle is enabled.
        """
        all_nodes: list = []
        temp = self.head
        while temp:
            all_nodes.append(temp)
            temp = temp.next

        if len(all_nodes) <= 1:
            # Only one song — nothing else to choose from
            self.play()
            return

        # Exclude the current node to prevent back-to-back repeats
        candidates = [n for n in all_nodes if n != self.current]
        self.current = random.choice(candidates)
        self.play()

    # ── Settings ──────────────────────────────────────────────────────────────

    def change_volume(self, vol: int) -> None:
        """
        Set the playback volume.

        Parameters
        ----------
        vol : int
            New volume level. Must be between 0 and 100 inclusive.
        """
        if 0 <= vol <= 100:
            self.volume = vol
            print(f"Volume set to {self.volume}")
        else:
            print("Invalid volume. Please enter a value between 0 and 100.")

    def toggle_repeat(self) -> None:
        """Flip repeat mode and print the updated state."""
        self.repeat = not self.repeat
        print("Repeat ON" if self.repeat else "Repeat OFF")

    def toggle_shuffle(self) -> None:
        """Flip shuffle mode and print the updated state."""
        self.shuffle = not self.shuffle
        print("Shuffle ON" if self.shuffle else "Shuffle OFF")

    # ── Display ───────────────────────────────────────────────────────────────

    def show_playlist(self) -> None:
        """
        Print every song in the playlist with its 1-based position number.

        The currently selected song is prefixed with ``->``.
        A short header shows the playlist name, shuffle state, and repeat state.
        """
        if not self.head:
            print("Playlist empty")
            return

        print(f"\nPlaylist : {self.name}")
        print(f"Shuffle  : {'ON' if self.shuffle else 'OFF'}  |  "
              f"Repeat : {'ON' if self.repeat else 'OFF'}")
        print()

        temp  = self.head
        index = 1
        while temp:
            marker = "->" if temp == self.current else "  "
            print(f"{marker} {index}. {temp.song}")
            temp  = temp.next
            index += 1

    def show_progress(self) -> None:
        """
        Display how long the current song has been playing.

        Combines ``elapsed_before_pause`` (time banked across previous
        play segments) with the live seconds since the last resume.
        When paused, only the banked time is shown.
        """
        if not self.current:
            print("No song selected.")
            return

        if self.is_playing and self.play_start_time:
            # Still playing: banked time + time since last resume
            total = self.elapsed_before_pause + (time.time() - self.play_start_time)
        else:
            # Paused: show only the banked total
            total = self.elapsed_before_pause

        minutes = int(total) // 60
        seconds = int(total) % 60

        print(f"  Song    : {self.current.song}")
        print(f"  Elapsed : {minutes}m {seconds:02d}s")
        print(f"  Status  : {'Playing' if self.is_playing else 'Paused'}")


# ──────────────────────────────────────────────────────────────────────────────
# Master library
# ──────────────────────────────────────────────────────────────────────────────

# Full catalogue of songs. Add or remove Song entries here to change
# what is available across the entire application.
master_library: list = [
    Song("Into the Night",            "Yasobi"),
    Song("Blinding Lights",           "The Weeknd"),
    Song("Jo Tum Mere Ho",            "Anuv Jain"),
    Song("Mockingbird",               "Eminem"),
    Song("Heat Waves",                "Glass Animals"),
    Song("Husn",                      "Anuv Jain"),
    Song("Rap God",                   "Eminem"),
    Song("Butter",                    "BTS"),
    Song("Die For You",               "The Weeknd"),
    Song("Fairytale",                 "Alexander Rybak"),

    Song("Golden Brown",              "The Stranglers"),
    Song("Back To Friends",           "Sombr"),
    Song("Freaks",                    "Surf Curse"),
    Song("Love Story",                "Indila"),
    Song("The Night We Met",          "Lord Huron"),
    Song("I Wanna Be Yours",          "Arctic Monkeys"),
    Song("Running Up That Hill",      "Kate Bush"),
    Song("Blue",                      "Yung Kai"),
    Song("Always The Sun",            "The Stranglers"),

    Song("Washing Machine Heart",     "Mitski"),
    Song("End of Beginning",          "Djo"),
    Song("Runaway",                   "AURORA"),
    Song("Sailor Song",               "Gigi Perez"),
    Song("Night Changes",             "One Direction"),
    Song("Tears",                     "Sabrina Carpenter"),
    Song("Shape of You",              "Ed Sheeran"),
    Song("World's Smallest Violin",   "AJR"),

    Song("Taste",                     "Sabrina Carpenter"),
    Song("Bed Chem",                  "Sabrina Carpenter"),
    Song("Coincidence",               "Sabrina Carpenter"),
    Song("We Don't Talk Anymore",     "Charlie Puth, Selena Gomez"),
    Song("STAY",                      "The Kid LAROI, Justin Bieber"),
    Song("Memories",                  "Maroon 5"),
    Song("A Thousand Years",          "Christina Perri"),
    Song("Die With A Smile",          "Lady Gaga, Bruno Mars"),
    Song("Arz Kiya Hai",              "Anuv Jain"),

    Song("Chubina - Super Slowed",    "East Duo"),
    Song("Daylight",                  "David Kushner"),
    Song("Dandelions",                "Ruth B."),
    Song("Under The Influence",       "Chris Brown"),
    Song("Love Nwantiti",             "CKay"),
    Song("Take Me To Church",         "Hozier"),
    Song("Summertime Sadness",        "Lana Del Rey"),
    Song("Save Your Tears",           "The Weeknd"),
    Song("Another Love",              "Tom Odell"),

    Song("7 Years",                   "Lukas Graham"),
    Song("Someone Like You",          "Adele"),
    Song("When I Was Your Man",       "Bruno Mars"),
    Song("Gul",                       "Anuv Jain"),
    Song("Baarishein",                "Anuv Jain"),
    Song("Meri Baaton Mein Tu",       "Anuv Jain"),
    Song("Alag Aasmaan",              "Anuv Jain"),
    Song("Alag Aasmaan - Acoustic",   "Anuv Jain"),

    Song("Levitating",                "Dua Lipa"),
    Song("Light Switch - Brighter Mix", "Charlie Puth"),
    Song("Beautiful Things - Slowed", "Benson Boone"),
    Song("Death Bed",                 "Powfu, Beabadoobee"),
    Song("Double Take",               "Dhruv"),
    Song("Interstellar",              "JERRIK DIZLOP"),
    Song("Lovely",                    "Billie Eilish, Khalid"),
]

# Global favorites list — shared across all playlists
favorites: list = []

# All playlists keyed by name — populated as the user creates them
playlists: dict = {}

# The playlist currently in use — None until the user creates or switches to one
current_playlist = None


# ──────────────────────────────────────────────────────────────────────────────
# Library: search and sort
# ──────────────────────────────────────────────────────────────────────────────

def search_song() -> None:
    """
    Search ``master_library`` by song title or artist name.

    Performs a case-insensitive substring match. Displays all matching
    results and, if the user chooses, adds a selected result to the
    currently active playlist.

    Notes
    -----
    The ``if not results`` check is intentionally placed *after* the
    loop so the full library is scanned before deciding nothing matched.
    """
    if not master_library:
        print("Master library empty.")
        return

    keyword = input("Enter song title or artist to search: ").lower()
    results = []

    # Collect every song whose title or artist contains the keyword
    for index, song in enumerate(master_library):
        if keyword in song.title.lower() or keyword in song.artist.lower():
            results.append((index, song))

    # Evaluate after the full loop — checking inside would give false negatives
    if not results:
        print("No songs found.")
        return

    print("\nSearch Results:")
    for i, (_, song) in enumerate(results, 1):
        print(f"  {i}. {song}")

    choice = input("\nAdd a song to current playlist? (y/n): ").lower()

    if choice == "y":
        if not current_playlist:
            print("No playlist selected.")
            return

        # Only prompt for a number if the user confirmed they want to add
        try:
            num           = int(input("Enter result number: "))
            selected_song = results[num - 1][1]
            current_playlist.add_song(selected_song)
        except (ValueError, IndexError):
            print("Invalid selection.")


def add_to_favorites() -> None:
    """
    Add the currently playing song to the global ``favorites`` list.

    Prevents duplicates by checking membership before appending.
    Reads ``current_playlist`` from the module-level global because
    this function is always called in a single-file context.
    """
    if not current_playlist or not current_playlist.current:
        print("No song is currently selected.")
        return

    song = current_playlist.current.song

    if song not in favorites:
        favorites.append(song)
        print(f"{song} added to favorites.")
    else:
        print("Already in favorites.")


def show_favorites() -> None:
    """
    Print every song in ``favorites``, numbered from 1.

    Prints a notice if the list is empty.
    """
    if not favorites:
        print("No favorite songs yet.")
        return

    print("\nFavorite Songs:")
    for i, song in enumerate(favorites, 1):
        print(f"  {i}. {song}")


def merge_sort(arr: list, key: str) -> list:
    """
    Sort a list of Song objects using recursive merge sort.

    Parameters
    ----------
    arr : list[Song]
        The list of songs to sort.
    key : str
        The Song attribute to sort by, e.g. ``'title'`` or ``'artist'``.

    Returns
    -------
    list[Song]
        A new sorted list. The original list is not mutated.

    Notes
    -----
    Time complexity  : O(n log n) in all cases.
    Space complexity : O(n) due to temporary lists created during merging.
    """
    if len(arr) <= 1:
        return arr   # base case — a list of 0 or 1 items is already sorted

    mid   = len(arr) // 2
    left  = merge_sort(arr[:mid], key)
    right = merge_sort(arr[mid:], key)

    return merge(left, right, key)


def merge(left: list, right: list, key: str) -> list:
    """
    Merge two sorted Song lists into a single sorted list.

    Comparison uses ``getattr(song, key).lower()`` so the sort is
    always case-insensitive regardless of the chosen key.

    Parameters
    ----------
    left : list[Song]
        First sorted half.
    right : list[Song]
        Second sorted half.
    key : str
        The Song attribute to compare, e.g. ``'title'`` or ``'artist'``.

    Returns
    -------
    list[Song]
        A merged, sorted list containing all elements from both halves.
    """
    result: list = []
    i = j = 0

    # Compare front elements of each half and take the smaller one
    while i < len(left) and j < len(right):
        if getattr(left[i], key).lower() <= getattr(right[j], key).lower():
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # One half may still have remaining elements — append them all
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def sort_master_library() -> None:
    """
    Sort ``master_library`` in-place, interactively.

    Prompts the user to choose a sort key (title or artist) then
    replaces ``master_library`` with the sorted result from
    ``merge_sort``.
    """
    global master_library

    print("Sort by:")
    print("  1. Title")
    print("  2. Artist")

    choice = input("Choose option: ")

    if choice == "1":
        master_library = merge_sort(master_library, "title")
        print("Sorted by title.")
    elif choice == "2":
        master_library = merge_sort(master_library, "artist")
        print("Sorted by artist.")
    else:
        print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Playlist management
# ──────────────────────────────────────────────────────────────────────────────

def create_new_playlist() -> None:
    """
    Create a new empty playlist and set it as the active one.

    Prompts the user for a name, validates it is non-empty and unique,
    then stores a new ``MusicPlayer`` in ``playlists`` and updates
    ``current_playlist``.
    """
    global current_playlist

    name = input("Enter playlist name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return
    if name in playlists:
        print("A playlist with that name already exists.")
        return

    playlists[name]  = MusicPlayer(name)
    current_playlist = playlists[name]
    print(f"Playlist '{name}' created and selected.")


def create_random_playlist() -> None:
    """
    Create a playlist pre-filled with random songs and make it active.

    Picks up to 10 unique songs from ``master_library`` using
    ``random.sample``, which guarantees no duplicate tracks within a
    single random playlist.

    Notes
    -----
    If ``master_library`` has fewer than 10 songs, all songs are added.
    """
    global current_playlist

    if not master_library:
        print("Master library is empty.")
        return

    name = input("Enter random playlist name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return
    if name in playlists:
        print("A playlist with that name already exists.")
        return

    new_playlist = MusicPlayer(name)

    # random.sample returns `count` unique items — no duplicate songs
    count        = min(10, len(master_library))
    random_songs = random.sample(master_library, count)

    for song in random_songs:
        new_playlist.add_song(song)

    playlists[name]  = new_playlist
    current_playlist = new_playlist
    print(f"Random playlist '{name}' created and selected.")


def switch_playlist() -> None:
    """
    Change the active playlist.

    Lists all available playlist names before prompting so the user
    does not need to remember exact names from memory.
    """
    global current_playlist

    if not playlists:
        print("No playlists available.")
        return

    show_all_playlists()
    name = input("Enter playlist name to switch to: ").strip()

    if name in playlists:
        current_playlist = playlists[name]
        print(f"Switched to '{name}'")
    else:
        print("Playlist not found.")


def show_all_playlists() -> None:
    """Print the names of every playlist stored in ``playlists``."""
    if not playlists:
        print("No playlists created.")
    else:
        print("\nAll Playlists:")
        for name in playlists:
            print(f"  - {name}")


def rename_playlist() -> None:
    """
    Rename an existing playlist, keeping all internal references in sync.

    Updates both the ``playlists`` dictionary key (external reference)
    and the ``MusicPlayer.name`` attribute (internal reference) so they
    always agree. Also refreshes ``current_playlist`` when the renamed
    playlist is the currently active one.
    """
    global current_playlist

    if not playlists:
        print("No playlists available.")
        return

    show_all_playlists()
    old_name = input("Enter the name of the playlist to rename: ").strip()

    if old_name not in playlists:
        print("Playlist not found.")
        return

    new_name = input("Enter the new name: ").strip()

    if not new_name:
        print("Name cannot be empty.")
        return
    if new_name in playlists:
        print("A playlist with that name already exists.")
        return

    # Pop under old key, update the internal name, re-insert under new key
    playlist_obj      = playlists.pop(old_name)
    playlist_obj.name = new_name
    playlists[new_name] = playlist_obj

    # If this was the active playlist, refresh the reference so it stays valid
    if current_playlist and current_playlist.name == new_name:
        current_playlist = playlists[new_name]

    print(f"Playlist renamed: '{old_name}' → '{new_name}'")


# ──────────────────────────────────────────────────────────────────────────────
# Sub-menus
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
    global current_playlist

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

        if choice == "1":
            create_new_playlist()

        elif choice == "2":
            create_random_playlist()

        elif choice == "3":
            switch_playlist()

        elif choice == "4":
            show_all_playlists()

        elif choice == "5":
            # Deletion is handled inline here so the global can be updated
            show_all_playlists()
            name = input("Enter playlist name to delete: ").strip()
            if name in playlists:
                del playlists[name]
                # Deselect if the deleted playlist was the active one
                if current_playlist and current_playlist.name == name:
                    current_playlist = None
                print(f"Playlist '{name}' deleted.")
            else:
                print("Playlist not found.")

        elif choice == "6":
            rename_playlist()

        elif choice == "0":
            break

        else:
            print("Invalid choice.")


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
    if not current_playlist:
        print("No playlist selected.")
        return

    while True:
        print(f"""
--- EDIT PLAYLIST ({current_playlist.name}) ---

1. View Songs
2. Add Song
3. Delete Song
4. Clear Playlist
0. Back
""")
        choice = input("Choose option: ")

        if choice == "1":
            current_playlist.show_playlist()

        elif choice == "2":
            # Print the full library so the user can select by number
            print("\nMaster Library:")
            for i, song in enumerate(master_library, 1):
                print(f"  {i}. {song}")
            try:
                num = int(input("Select song number: "))
                current_playlist.add_song(master_library[num - 1])
            except (ValueError, IndexError):
                print("Invalid selection.")

        elif choice == "3":
            current_playlist.show_playlist()
            try:
                pos = int(input("Enter song number to delete: "))
                current_playlist.delete_song(pos)
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "4":
            current_playlist.clear()

        elif choice == "0":
            break

        else:
            print("Invalid choice.")


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
    if not current_playlist:
        print("No playlist selected.")
        return

    while True:
        # Check whether the current song has finished before rendering the menu.
        # This is the auto-advance hook — no threads needed.
        current_playlist.check_and_advance()

        print(f"""
--- PLAYBACK MENU ({current_playlist.name}) ---

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

        if   choice == "1": current_playlist.play()
        elif choice == "2": current_playlist.resume()
        elif choice == "3": current_playlist.next_song()
        elif choice == "4": current_playlist.previous_song()
        elif choice == "5": current_playlist.pause()
        elif choice == "7": current_playlist.toggle_repeat()
        elif choice == "8": current_playlist.toggle_shuffle()
        elif choice == "9": current_playlist.show_progress()

        elif choice == "6":
            # Volume requires parsing — wrap in try/except for safety
            try:
                vol = int(input("Enter volume (0-100): "))
                current_playlist.change_volume(vol)
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "0":
            break

        else:
            print("Invalid choice.")


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

        if   choice == "1": add_to_favorites()
        elif choice == "2": show_favorites()
        elif choice == "0": break
        else:               print("Invalid choice.")


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

        if   choice == "1": search_song()
        elif choice == "2": sort_master_library()
        elif choice == "0": break
        else:               print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Main menu
# ──────────────────────────────────────────────────────────────────────────────

def menu() -> None:
    """
    Display the main menu and route user input to sub-menus.

    A live status header is printed at the top of every loop iteration
    so the user can always see the active playlist, playback state,
    volume, shuffle, and repeat settings without navigating anywhere.

    Options
    -------
    1  Playlist Options  — create, switch, rename, or delete playlists.
    2  Edit Playlist     — add, remove, or clear songs.
    3  Playback Controls — play, pause, skip, volume, shuffle, repeat.
    4  Library Options   — search or sort the master library.
    5  Favorites         — add the current song or view saved favorites.
    0  Exit the application.
    """
    while True:
        # Snapshot the active playlist into a short alias for the header
        cp = current_playlist

        print(f"""
===== MUSIC PLAYER =====
Current Playlist : {cp.name        if cp else 'None'}
Now Playing      : {'ON'           if cp and cp.is_playing else 'OFF'}
Volume           : {cp.volume      if cp else 'N/A'}
Shuffle          : {'ON'           if cp and cp.shuffle    else 'OFF'}  |  \
Repeat : {'ON' if cp and cp.repeat else 'OFF'}

1. Playlist Options
2. Edit Current Playlist
3. Playback Controls
4. Library Options
5. Favorites
0. Exit
""")

        choice = input("Choose option: ")

        if   choice == "1": playlist_menu()
        elif choice == "2": edit_playlist_menu()
        elif choice == "3": playback_menu()
        elif choice == "4": library_menu()
        elif choice == "5": favorites_menu()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

# Guard ensures menu() only runs when this file is executed directly.
# Importing this file as a module (e.g. for testing) will not trigger it.
if __name__ == "__main__":
    menu()
