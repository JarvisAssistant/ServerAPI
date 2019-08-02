// 2. This code loads the IFrame Player API code asynchronously.
var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// 3. This function creates an <iframe> (and YouTube player)
//    after the API code downloads.
var player;
function onYouTubeIframeAPIReady() {
player = new YT.Player('player', {
  height: '390',
  width: '640',
  videoId: 'M7lc1UVf-VE',
  events: {
    'onReady': onPlayerReady
  }
});
}

// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {
	listen()
    update_state()
}

function listen() {
    $.ajax({
      url: '/poll',
      success: function(data) {
        if (data.type == 'play') {
          player.loadVideoById(data.id);
        } else if (data.type == 'stop') {
          player.stopVideo();
        } else if (data.type == 'pause') {
          player.pauseVideo();
        } else if (data.type == 'resume') {
          player.playVideo();
        }

        listen();
      },
      error: function() {
        setTimeout(listen, 1000);
      },
      timeout: 0 //500000
  });
}

function update_state() {
    var ytplayer_state = {
        is_playing: player.getPlayerState() == 1,
        position_sec: player.getCurrentTime(),
        duration_sec: player.getDuration(),
    }
    $.ajax({
      url: '/update_ytplayer_state',
      type: 'post',
      contentType: 'application/json',
      data: JSON.stringify(ytplayer_state),
      success: function(data) {
        setTimeout(update_state, 100);
      },
      error: function(xhr, status, error) {
        console.log(xhr.responseText)
        setTimeout(update_state, 1000);
      },
      timeout: 1000
  });
}
