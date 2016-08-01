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


function Sound(title, detail, duration, streams) {
    this.title = title;
    this.detail = detail;
    this.duration = duration;
    this.streams = streams.splice ? streams.sort() : [streams];
}

Sound.prototype = {
    title: '',
    detail: '',
    streams: undefined,
    duration: undefined,
    on_air_url: undefined,

    item: undefined,

    get seekable() {
        return this.duration != undefined;
    },
}


function PlayerPlaylist(player) {
    this.player = player;
    this.playlist = player.player.querySelector('.playlist');
    this.item_ = player.player.querySelector('.playlist .item');
    this.sounds = []
}

PlayerPlaylist.prototype = {
    sounds: undefined,

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

    add: function(sound, container) {
        var sound_ = this.find(sound.streams);
        if(sound_)
            return sound_;

        var item = this.item_.cloneNode(true);
        item.removeAttribute('style');

        item.querySelector('.title').innerHTML = sound.title;
        if(sound.seekable)
            item.querySelector('.duration').innerHTML =
                duration_str(sound.duration);
        if(sound.detail)
            item.querySelector('.detail').href = sound.detail;

        item.sound = sound;
        sound.item = item;

        var self = this;
        item.querySelector('.action.remove').addEventListener(
            'click', function(event) { self.remove(sound); }, false
        );
        item.addEventListener('click', function(event) {
            if(event.target.className.indexOf('action') != -1)
                return;
            self.player.select(sound, true)
        }, false);

        (container || this.playlist).appendChild(item);
        this.sounds.push(sound);
        this.save();
        return sound;
    },

    remove: function(sound) {
        var index = this.sounds.indexOf(sound);
        if(index != -1)
            this.sounds.splice(index,1);
        this.playlist.removeChild(sound.item);
        this.save();
    },

    save: function() {
        var list = [];
        for(var i in this.sounds) {
            var sound = Object.assign({}, this.sounds[i])
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
                              sound.streams)
            this.add(sound, container)
        }
        this.playlist.appendChild(container);
    },
}


function Player(id) {
    this.store = new Store('player');

    // html sounds
    this.player = document.getElementById(id);
    this.audio = this.player.querySelector('audio');
    this.on_air = this.player.querySelector('.on_air');
    this.controls = {
        duration: this.player.querySelector('.controls .duration'),
        progress: this.player.querySelector('progress'),
        single: this.player.querySelector('input.single'),
    }

    this.playlist = new PlayerPlaylist(this);
    this.playlist.load();

    this.init_events();
    this.load();
}

Player.prototype = {
    /// current item being played
    sound: undefined,

    init_events: function() {
        var self = this;

        function time_from_progress(event) {
            bounding = self.controls.progress.getBoundingClientRect()
            offset = (event.clientX - bounding.left);
            return offset * self.audio.duration / bounding.width;
        }

        function update_info() {
            var controls = self.controls;
            // progress
            if(!self.sound || !self.sound.seekable ||
                    self.audio.duration == Infinity) {
                controls.duration.innerHTML = '';
                controls.progress.value = 0;
                return;
            }

            var pos = self.audio.currentTime;
            controls.progress.value = pos;
            controls.progress.max = self.audio.duration;
            controls.duration.innerHTML = duration_str(pos);
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
                self.next(true);
        }, false);

        // progress
        progress = this.controls.progress;
        progress.addEventListener('click', function(event) {
            player.audio.currentTime = time_from_progress(event);
        }, false);

        progress.addEventListener('mouseout', update_info, false);

        progress.addEventListener('mousemove', function(event) {
            if(self.audio.duration == Infinity)
               return;

            var pos = time_from_progress(event);
            self.controls.duration.innerHTML = duration_str(pos);
        }, false);
    },

    update_on_air: function(url) {
        if(!url) {
            // TODO HERE
        }

        var self = this;
        var req = new XMLHttpRequest();
        req.open('GET', url, true);
        req.onreadystatechange = function() {
            if(req.readyState != 4 || (req.status != 200 && req.status != 0))
                return;

            var data = JSON.parse(req.responseText)
            if(data.type == 'track') {
                self.on_air.querySelector('.info').innerHTML = '♫';
                self.on_air.querySelector('.title') =
                    (data.artist || '') + ' — ' + (data.title);
                self.on_air.querySelector('.url').removeAttribute('href');
            }
            else {
                self.on_air.querySelector('.info').innerHTML = '';
                self.on_air.querySelector('.title').innerHTML = data.title;
                self.on_air.querySelector('.url').setAttribute('href', data.url);
            }

            if(timeout)
                window.setTimeout(function() {
                    self.update_on_air(url);
                }, 60*1000);
        };
        req.send();
    },

    play: function() {
        if(this.audio.paused)
            this.audio.play();
        else
            this.audio.pause();
    },

    unselect: function(sound) {
        sound.item.removeAttribute('selected');
    },

    __mime_type: function(path) {
        ext = path.substr(path.lastIndexOf('.')+1);
        return 'audio/' + ext;
    },

    select: function(sound, play = true) {
        if(this.sound == sound) {
            if(play)
                this.play();
            return;
        }

        if(this.sound)
            this.unselect(this.sound);

        this.audio.pause();

        // streams as <source>
        var sources = this.audio.querySelectorAll('source');
        for(var i = 0; i < sources.length; i++) {
            this.audio.removeChild(sources[i]);
        }

        streams = sound.streams;
        for(var i = 0; i < streams.length; i++) {
            var source = document.createElement('source');
            source.src = streams[i];
            source.type = this.__mime_type(source.src);
            this.audio.appendChild(source);
        }
        this.audio.load();

        // attributes
        this.sound = sound;
        sound.item.setAttribute('selected', 'true');

        if(sound.seekable)
            this.player.setAttribute('seekable', 'true');
        else
            this.player.removeAttribute('seekable');

        // play
        if(play)
            this.play();
    },

    next: function() {
        var index = this.playlist.sounds.indexOf(this.sound);
        if(index < 0)
            return;

        index++;
        if(index < this.playlist.sounds.length)
            this.select(this.playlist.sounds[index], true);
    },

    save: function() {
        this.store.set('player', {
            single: this.controls.single.checked,
            sound: this.sound && this.sound.streams,
        });
    },

    load: function() {
        var data = this.store.get('player');
        this.controls.single.checked = data.single;
        if(data.sound)
            this.sound = this.playlist.find(data.sound);
    },
}


