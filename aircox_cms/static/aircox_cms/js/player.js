// TODO
// - live streams as item;
// - add to playlist button
//

/// Return a human-readable string from seconds
function duration_str(seconds) {
    seconds = Math.floor(seconds);
    var hours = Math.floor(seconds / 3600);
    seconds -= hours * 3600;
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;

    var str = hours ? (hours < 10 ? '0' + hours : hours) + ':' : '';
    str += (minutes < 10 ? '0' + minutes : minutes) + ':';
    str += (seconds < 10 ? '0' + seconds : seconds);
    return str;
}


function Sound(title, detail, duration, streams, cover, on_air) {
    this.title = title;
    this.detail = detail;
    this.duration = duration;
    this.streams = streams.splice ? streams.sort() : [streams];
    this.cover = cover;
    this.on_air = on_air;
}

Sound.prototype = {
    title: '',
    detail: '',
    streams: undefined,
    duration: undefined,
    cover: undefined,
    on_air: false,

    item: undefined,
    position_item: undefined,

    get seekable() {
        return this.duration != undefined;
    },

    make_item: function(playlist, base_item) {
        if(this.item)
            return;

        var item = base_item.cloneNode(true);
        item.removeAttribute('style');

        item.querySelector('.title').innerHTML = this.title;
        if(this.seekable)
            item.querySelector('.duration').innerHTML =
                duration_str(this.duration);
        if(this.detail)
            item.querySelector('.detail').href = this.detail;
        if(playlist.player.show_cover && this.cover)
            item.querySelector('img.cover').src = this.cover;

        item.sound = this;
        this.item = item;
        this.position_item = item.querySelector('.position');

        // events
        var self = this;
        item.querySelector('.action.remove').addEventListener(
            'click', function(event) { playlist.remove(self); }, false
        );

        item.querySelector('.action.add').addEventListener(
            'click', function(event) {
                player.playlist.add(new Sound(
                    title = self.title,
                    detail = self.detail,
                    duration = self.duration,
                    streams = self.streams,
                    cover = self.cover,
                    on_air = self.on_air
                ));
            }, false
        );

        item.addEventListener('click', function(event) {
            if(event.target.className.indexOf('action') != -1)
                return;
            playlist.select(self, true)
        }, false);
    },
}


function Playlist(player) {
    this.player = player;
    this.playlist = player.player.querySelector('.playlist');
    this.item_ = player.player.querySelector('.playlist .item');
    this.sounds = []
}

Playlist.prototype = {
    on_air: undefined,
    sounds: undefined,
    sound: undefined,

    /// Find a sound by its streams, and return it if found
    find: function(streams) {
        streams = streams.splice ? streams.sort() : streams;

        return this.sounds.find(function(sound) {
            // comparing array
            if(!sound.streams || sound.streams.length != streams.length)
                return false;

            for(var i = 0; i < streams.length; i++)
                if(sound.streams[i] != streams[i])
                    return false;
            return true
        });
    },

    add: function(sound, container, position) {
        var sound_ = this.find(sound.streams);
        if(sound_)
            return sound_;

        if(sound.on_air)
            this.on_air = sound;

        sound.make_item(this, this.item_);

        container = container || this.playlist;
        if(position != undefined) {
            container.insertBefore(sound.item, container.children[position]);
            this.sounds.insert(position, 0, sound.item);
        }
        else {
            container.appendChild(sound.item);
            this.sounds.push(sound);
        }
        this.save();
        return sound;
    },

    remove: function(sound) {
        var index = this.sounds.indexOf(sound);
        if(index != -1)
            this.sounds.splice(index,1);
        this.playlist.removeChild(sound.item);
        this.save();

        this.player.stop()
        this.next(false);
    },

    select: function(sound, play = true) {
        this.player.playlist = this;
        if(this.sound == sound) {
            if(play)
                this.player.play();
            return;
        }

        if(this.sound)
            this.unselect(this.sound);
        this.sound = sound;

        // audio
        this.player.load_sound(this.sound);

        // attributes
        var container = this.player.player;
        sound.item.setAttribute('selected', 'true');

        if(!sound.on_air)
            sound.item.querySelector('.content').parentNode.appendChild(
                this.player.progress.item //,
                // sound.item.querySelector('.content .duration')
            )

        if(sound.seekable)
            container.setAttribute('seekable', 'true');
        else
            container.removeAttribute('seekable');

        // play
        if(play)
            this.player.play();
    },

    unselect: function(sound) {
        sound.item.removeAttribute('selected');
    },

    next: function(play = true) {
        var index = this.sounds.indexOf(this.sound);
        if(index < 0)
            return;

        index++;
        if(index < this.sounds.length)
            this.select(this.sounds[index]);
    },

    // storage
    save: function() {
        var list = [];
        for(var i in this.sounds) {
            var sound = Object.assign({}, this.sounds[i])
            if(sound.on_air)
                continue;
            delete sound.item;
            list.push(sound);
        }
        this.player.store.set('playlist', list);
    },

    load: function() {
        var list = this.player.store.get('playlist');
        var container = document.createDocumentFragment();
        for(var i in list) {
            var sound = list[i];
            sound = new Sound(sound.title, sound.detail, sound.duration,
                              sound.streams, sound.cover, sound.on_air)
            this.add(sound, container)
        }
        this.playlist.appendChild(container);
    },
}

var ActivePlayer = null;

function Player(id, on_air_url, show_cover) {
    this.id = id;
    this.on_air_url = on_air_url;
    this.show_cover = show_cover;

    this.store = new Store('player_' + id);

    // html sounds
    this.player = document.getElementById(id);
    this.audio = this.player.querySelector('audio');
    this.on_air = this.player.querySelector('.on_air');
    this.progress = {
        item: this.player.querySelector('.controls .progress'),
        bar: this.player.querySelector('.controls .progress progress'),
        duration: this.player.querySelector('.controls .progress .duration')
    }

    this.controls = {
        single: this.player.querySelector('input.single'),
    }

    this.playlist = new Playlist(this);
    this.playlist.load();

    this.init_events();
    this.load();
}

Player.prototype = {
    /// current item being played
    sound: undefined,
    on_air_url: undefined,

    get sound() {
        return this.playlist.sound;
    },

    init_events: function() {
        var self = this;

        function time_from_progress(event) {
            bounding = self.progress.bar.getBoundingClientRect()
            offset = (event.clientX - bounding.left);
            return offset * self.audio.duration / bounding.width;
        }

        function update_info() {
            var progress = self.progress;
            var pos = self.audio.currentTime;
            var position = self.sound.position_item;

            // progress
            if(!self.audio || !self.audio.seekable ||
                    !pos || self.audio.duration == Infinity)
            {
                position.innerHTML = '';
                progress.bar.value = 0;
                return;
            }

            progress.bar.value = pos;
            progress.bar.max = self.audio.duration;
            position.innerHTML = duration_str(pos);
        }

        // audio
        this.audio.addEventListener('playing', function() {
            self.player.setAttribute('state', 'playing');
        }, false);

        this.audio.addEventListener('pause', function() {
            self.player.setAttribute('state', 'paused');
        }, false);

        this.audio.addEventListener('loadstart', function() {
            self.player.setAttribute('state', 'loading');
        }, false);

        this.audio.addEventListener('loadeddata', function() {
            self.player.removeAttribute('state');
        }, false);

        this.audio.addEventListener('timeupdate', update_info, false);

        this.audio.addEventListener('ended', function() {
            self.player.removeAttribute('state');
            if(!self.controls.single.checked)
                self.playlist.next(true);
        }, false);

        // progress
        progress = this.progress.bar;
        progress.addEventListener('click', function(event) {
            self.audio.currentTime = time_from_progress(event);
            event.preventDefault();
            event.stopImmediatePropagation();
        }, false);

        progress.addEventListener('mouseout', update_info, false);

        progress.addEventListener('mousemove', function(event) {
            if(self.audio.duration == Infinity || isNaN(self.audio.duration))
               return;

            var pos = time_from_progress(event);
            var position = self.sound.position_item;
            position.innerHTML = duration_str(pos);
        }, false);
    },

    update_on_air: function() {
        if(!this.on_air_url)
            return;

        var self = this;
        window.setTimeout(function() {
            self.update_on_air();
        }, 60*2000);

        if(!this.playlist.on_air)
            return;

        var req = new XMLHttpRequest();
        req.open('GET', this.on_air_url, true);
        req.onreadystatechange = function() {
            if(req.readyState != 4 || (req.status != 200 &&
                    req.status != 0))
                return;

            var data = JSON.parse(req.responseText)
            if(data.type == 'track')
                data = {
                    title: '♫ ' + (data.artist ? data.artist + ' — ' : '') +
                           data.title,
                    url: ''
                }
            else
                data = {
                    title: data.title,
                    info: '',
                    url: data.url
                }

            var on_air = self.playlist.on_air;
            on_air = on_air.item.querySelector('.content');

            if(data.url)
                on_air.innerHTML =
                    '<a href="' + data.url + '">' + data.title + '</a>';
            else
                on_air.innerHTML = data.title;
        };
        req.send();
    },

    play: function() {
        if(ActivePlayer && ActivePlayer != this) {
            ActivePlayer.stop();
        }
        ActivePlayer = this;

        if(this.audio.paused)
            this.audio.play();
        else
            this.audio.pause();
    },

    stop: function() {
        this.audio.pause();
        this.player.removeAttribute('state');
    },

    __mime_type: function(path) {
        ext = path.substr(path.lastIndexOf('.')+1);
        return 'audio/' + ext;
    },

    load_sound: function(sound) {
        var audio = this.audio;
        audio.pause();

        var sources = audio.querySelectorAll('source');
        for(var i = 0; i < sources.length; i++)
            audio.removeChild(sources[i]);

        streams = sound.streams;
        for(var i = 0; i < streams.length; i++) {
            var source = document.createElement('source');
            source.src = streams[i];
            source.type = this.__mime_type(source.src);
            audio.appendChild(source);
        }
        audio.load();
    },

    save: function() {
        // TODO: move stored sound into playlist
        this.store.set('player', {
            single: this.controls.single.checked,
            sound: this.playlist.sound && this.playlist.sound.streams,
        });
    },

    load: function() {
        var data = this.store.get('player');
        if(!data)
            return;
        this.controls.single.checked = data.single;
        if(data.sound)
            this.playlist.sound = this.playlist.find(data.sound);
    },
}


