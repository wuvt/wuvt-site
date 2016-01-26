// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

var streams = [
    ['audio/ogg', "http://engine.wuvt.vt.edu:8000/wuvt.ogg"],
    ['audio/aac', "http://engine.wuvt.vt.edu:8000/wuvt.aac"]
];
var streamPlaying = false;

function initPlayer() {
    var playBtn = $('<button>');
    playBtn.attr('title', "Play");
    playBtn.attr('id', "stream_btn");
    playBtn.text("Play/Stop");
    $('#robot').append(playBtn);

    var volBtn = $('<button>');
    volBtn.attr('title', "Volume Control");
    volBtn.attr('id', "volume_btn");
    volBtn.text("Volume Control");
    $('#robot').append(volBtn);

    var audioTag = document.createElement('audio');

    for(i in streams) {
        var stream = streams[i];
        if(audioTag.canPlayType(stream[0])) {
            initStream(stream[1]);
            return;
        }
    }

    $('#stream_btn').addClass('disabled');
    $('#stream_btn').click(warnBrokenPlayer);

    $('#volume_btn').addClass('disabled');
    $('#volume_btn').click(warnBrokenPlayer);
}

function initStream(streamUrl) {
    // This doesn't work on Chrome for Android:
    // https://code.google.com/p/chromium/issues/detail?id=178297

    $('#stream_btn').click(function() {
        if(!streamPlaying) {
            var stream = document.createElement('audio');
            $(stream).attr('id', "wuvt_stream");
            $(stream).attr('src', streamUrl);
            $(stream).attr('autoplay', "autoplay");
            $('body').append(stream);

            stream.addEventListener('play', function() {
                $('#stream_btn').addClass('playing');
                $('#stream_btn').attr('title', "Stop");
                $('#stream_btn').removeAttr('disabled');
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

            // display an alert after 5 seconds if the stream hasn't started
            window.setTimeout(function() {
                if(streamPlaying && !$('#stream_btn').hasClass('playing')) {
                    alert("Streaming problems? Check the Listen Live page for other ways to listen to WUVT!");
                }
            }, 5000);

            streamPlaying = true;
            $('#stream_btn').attr('title', "Buffering...");
            $('#stream_btn').attr('disabled', "disabled");
        }
        else {
            $('#wuvt_stream').attr('src', "");
            $('#wuvt_stream').remove();

            streamPlaying = false;
            $('#stream_btn').removeClass('playing');
            $('#stream_btn').attr('title', "Play");

            $('#volume_box').removeClass('visible');
        }

        return false;
    });

    initVolume();
}

function initVolume() {
    var volbox = document.createElement('div');
    $(volbox).attr('id', "volume_box");

    // create volume slider
    var slider = document.createElement('div');
    $(slider).attr('id', "volume_slider");
    $(volbox).append(slider);

    // create mute button
    var mutebtn = document.createElement('button');
    $(mutebtn).attr('id', "volume_mute_btn");
    $(mutebtn).attr('title', "Mute");
    $(mutebtn).text("Mute");
    $(volbox).append(mutebtn);

    $('#mainheader').append(volbox);

    // adjust volume box placement
    $(document).ready(positionVolumeBox);
    $(document).on('pageChange', positionVolumeBox);

    $('#volume_btn').click(function() {
        $('#volume_btn').toggleClass('active');
        $('#volume_box').toggleClass('visible');
    });

    $('#volume_slider').slider({
        'orientation': "vertical",
        'value': 1,
        'step': 0.05,
        'range': "min",
        'max': 1,
        'animate': false,
        'slide': function(e, slider) {
            $('#wuvt_stream').prop('muted', false);
            $('#wuvt_stream').prop('volume', slider.value);
        },
    });

    $('#volume_mute_btn').click(function() {
        if(!$('#wuvt_stream').prop('muted')) {
            $('#wuvt_stream').prop('muted', true);
            $('#volume_slider').slider('option', 'value', 0);
        }
        else {
            $('#wuvt_stream').prop('muted', false);
            $('#volume_slider').slider('option', 'value',
                $('#wuvt_stream').prop('volume'));
        }
    });
}

function positionVolumeBox() {
    $('#volume_btn').removeClass('active');
    $('#volume_box').removeClass('visible');

    var btn = $('#volume_btn');
    var offsetTop = btn.offset().top + btn.outerHeight();
    var offsetLeft = btn.offset().left + (btn.outerWidth() / 2) -
        ($('#volume_box').outerWidth() / 2);
    $('#volume_box').css('top', offsetTop + "px");
    $('#volume_box').css('left', offsetLeft + "px");
}

function warnBrokenPlayer() {
    alert("Sorry, the WUVT live stream player is not supported by your browser. Please see the Listen Live page for other ways to listen to WUVT, or switch to Google Chrome or Mozilla Firefox.");
}

// @license-end
