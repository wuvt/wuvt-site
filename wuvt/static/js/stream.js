var streamUrl = "http://engine.collegemedia.vt.edu:8000/wuvt.ogg";
var streamPlaying = false;

function initPlayer() {
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
            stream.addEventListener("error", function() {
                $('#wuvt_stream').attr('src', "");
                $('#wuvt_stream').attr('src', streamUrl);
                $('#wuvt_stream').trigger('play');
            });

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
        }

        return false;
    });
}
