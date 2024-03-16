// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

var streams = [
    ['audio/aac', "https://stream.wuvt.vt.edu/wuvt.aac"],
    ['audio/ogg', "https://stream.wuvt.vt.edu/wuvt.ogg"]
];
var streamPlaying = false;
var defaultVolume = 50;

function initPlayer() {
    var playBtn = $('<button>');
    playBtn.attr('title', "Play");
    playBtn.attr('id', "stream_btn");
    var playIcon = $('<span>');
    playIcon.addClass('glyphicon');
    playIcon.addClass('glyphicon-play');
    playBtn.append(playIcon);
    $('#robot').append(playBtn);

    var volBtnWrapper = $('<div>');
    volBtnWrapper.attr('id', "vol_btn_wrapper");
    var volBtn = $('<button>');
    volBtn.attr('title', "Volume Control");
    volBtn.attr('id', "volume_btn");
    var volIcon = $('<span>');
    volIcon.addClass('glyphicon');
    volIcon.addClass('glyphicon-volume-down');
    volBtn.append(volIcon);
    volBtnWrapper.append(volBtn);
    $('#robot').append(volBtnWrapper);

    var audioTag = document.createElement('audio');

    for(i in streams) {
        var stream = streams[i];
        if(audioTag.canPlayType(stream[0])) {
            initStream(stream[0], stream[1]);
            return;
        }
    }

    $('#stream_btn').addClass('disabled');
    $('#stream_btn').click(warnBrokenPlayer);

    $('#volume_btn').addClass('disabled');
    $('#volume_btn').click(warnBrokenPlayer);
}

function initStream(streamMime, streamUrl) {
    $('#stream_btn').click(function() {
        if(!streamPlaying) {
            var stream = document.createElement('audio');
            $(stream).attr('id', "wuvt_stream");
            $(stream).attr('type', streamMime);
            $(stream).attr('src', streamUrl);
            $(stream).prop('volume', $('#volume_slider').val() / 100);
            $('body').append(stream);

            stream.addEventListener('play', function() {
                $('#stream_btn').addClass('playing');
                $('#stream_btn').attr('title', "Stop");
                $('#stream_btn span').removeClass('glyphicon-play');
                $('#stream_btn span').addClass('glyphicon-stop');
                $('#stream_btn').prop('disabled', false);
            });

            // workaround to deal with playback stopping when metadata changes
            // https://bugzil.la/455165
            stream.addEventListener("ended", function() {
                $('#wuvt_stream').attr('src', "");
                $('#wuvt_stream').attr('src', streamUrl);
            });

            // chrome workaround for the same thing
            // https://code.google.com/p/chromium/issues/detail?id=175281
            stream.addEventListener("error", function() {
                $('#wuvt_stream').attr('src', "");
                $('#wuvt_stream').attr('src', streamUrl);
                $('#wuvt_stream').trigger('play');
            });

            stream.play();

            // display an alert after 5 seconds if the stream hasn't started
            window.setTimeout(function() {
                if(streamPlaying && !$('#stream_btn').hasClass('playing')) {
                    alert("Streaming problems? Check the Listen Live page for other ways to listen to WUVT!");
                }
            }, 5000);

            streamPlaying = true;
            $('#stream_btn').attr('title', "Buffering...");
            $('#stream_btn').prop('disabled', true);
        }
        else {
            $('#wuvt_stream').attr('src', "");
            $('#wuvt_stream').remove();

            streamPlaying = false;
            $('#stream_btn').removeClass('playing');
            $('#stream_btn').attr('title', "Play");
            $('#stream_btn span').removeClass('glyphicon-stop');
            $('#stream_btn span').addClass('glyphicon-play');

            // restore state of volume controls to default
            $('#volume_btn').removeClass('active');
            $('#volume_box').removeClass('visible');
            $('#volume_slider').prop('disabled', false);
            $('#volume_mute_btn').removeClass('active');
        }

        return false;
    });

    initVolume();
}

function initVolume() {
    var volbox = document.createElement('div');
    $(volbox).attr('id', "volume_box");

    // create volume slider
    var slider = document.createElement('input');
    $(slider).attr('id', "volume_slider");
    $(slider).attr('type', 'range');
    $(slider).attr('min', '0');
    $(slider).attr('max', '100');
    $(slider).attr('step', '1');
    $(slider).val(defaultVolume);
    $(volbox).append(slider);

    // create mute button
    var muteBtn = document.createElement('button');
    $(muteBtn).attr('id', "volume_mute_btn");
    $(muteBtn).attr('title', "Mute");
    var muteIcon = document.createElement('span');
    $(muteIcon).addClass('glyphicon');
    $(muteIcon).addClass('glyphicon-volume-off');
    $(muteBtn).append(muteIcon);
    $(volbox).append(muteBtn);

    $('#robot').append(volbox);

    $('#volume_btn').on('click', function() {
        $('#volume_btn').toggleClass('active');
        $('#volume_box').toggleClass('visible');
    });

    function updateVolume(e) {
        $('#wuvt_stream').prop('muted', false);
        $('#wuvt_stream').prop('volume', this.value / 100);
    }

    $('#volume_slider').on('change', updateVolume);
    $('#volume_slider').on('input', updateVolume);

    $('#volume_mute_btn').on('click', function() {
        if(!$('#volume_slider').prop('disabled')) {
            $('#wuvt_stream').prop('muted', true);
            $('#volume_slider').prop('disabled', true);
            $('#volume_mute_btn').addClass('active');
        }
        else {
            $('#wuvt_stream').prop('muted', false);
            $('#volume_slider').prop('disabled', false);
            $('#volume_mute_btn').removeClass('active');
        }
    });
}

function warnBrokenPlayer() {
    alert("Sorry, the WUVT live stream player is not supported by your browser. Please see the Listen Live page for other ways to listen to WUVT, or switch to Google Chrome or Mozilla Firefox.");
}

// @license-end
