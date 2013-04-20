function layout() {
  // 计算需要多少方块来填充屏幕
  var cube_size = CUBE_SIZE,
      sw = $(window).width(), 
      sh = $(window).height(),
      cube_real_size = cube_size + 1,
      cube_each_row = parseInt( sw / cube_real_size ) + 1,
      cube_rows = parseInt( sh / cube_real_size ) + 1;

  // 总块数
  CUBE_TOTAL = cube_rows * cube_each_row;
  // 以及尺寸
  WALL_WIDTH = cube_each_row * cube_size,
  WALL_HEIGHT = cube_rows * cube_size;

  // 给#wall定位，让wall全屏居中
  var wall = $('<div>').attr('id', 'wall').css({
    'top'  : '-' + (cube_rows * cube_real_size - sh) / 2 + 'px',
    'left' : '-' + (cube_each_row * cube_real_size - sw) / 2 + 'px'
  });

  // 添加方块
  for( var i = 0; i < cube_rows; i++ ) {
    for( var j = 0; j < cube_each_row; j++ ) {
      var cube = $('<div>').attr('id', 'cube-' + i + '-' + j).addClass('cube').css({
        'width' : cube_size + 'px',
        'height': cube_size + 'px',
        'left'  : cube_size * j + j + 'px',
        'top'   : cube_size * i + i + 'px'
      });
      // 每个方块里面带两个缓冲层来做动画效果
      $('<div>').addClass('buffer_a').css({
        'width'              : cube_size, 
        'height'             : cube_size,
        'backgroundPosition' : '-' + j * cube_size + 'px -' + i * cube_size + 'px'
      }).appendTo(cube);
      $('<div>').addClass('buffer_b').css({
        'width'              : cube_size, 
        'height'             : cube_size,
        'backgroundPosition' : '-' + j * cube_size + 'px -' + i * cube_size + 'px'
      }).appendTo(cube);
      cube.appendTo(wall);
    }
  }

  // 插入DOM
  wall.prependTo($('#wall-wrapper').empty());
  // 初始化缓冲层
  BUFFER_CURRENT = $('.buffer_a');
  BUFFER_BACK = $('.buffer_b');
}

function prepareImage() {
  // 总图片数量
  IMAGE_TOTAL = $('.origin').length;
  IMAGE_CURRENT = 0;

  // 请求图片的参数
  var params = '&w=' + WALL_WIDTH + '&h=' + WALL_HEIGHT + '&zc=2&q=85&cc=202020';

  // 读取图片信息
  IMAGES = [];
  $('.origin').each(function(){
    var image = {};
    // 如果图片比屏幕大就不用缩放，否则就缩放后再读取
    if( $(this).width() > WALL_WIDTH && $(this).height() > WALL_HEIGHT )
      image.src = this.src;
    else
      image.src = 'timthumb.php?src=' + this.src + params;

    IMAGES.push(image);
  });
}

function animation() {
  // 动画时间就1s吧
  DURATION = DURATION ? DURATION : 1;
  
  doAnimation();
  // 开始循环
  LOOP = setInterval(doAnimation, DELAY * 1000);
}

function doAnimation() {
  // 切换图片
  IMAGE_CURRENT++;
  if( IMAGE_CURRENT >= IMAGE_TOTAL ) IMAGE_CURRENT = 0;

  // 切换缓冲层 
  var BUFFER_TMP = BUFFER_CURRENT;
  BUFFER_CURRENT = BUFFER_BACK;
  BUFFER_BACK = BUFFER_TMP;

  // 更新缓冲层
  BUFFER_CURRENT.css({
    'backgroundImage': 'url(\'' + IMAGES[IMAGE_CURRENT].src + '\')'
  });
  // 随机选一种效果，翻转！
  fx( ANIMATIONS[random(ANIMATION_TOTAL)] );
}

$(window).bind('load', function() {
  layout();
  prepareImage();
  animation();
});
$(window).resize(function(){
  layout();
  prepareImage();
});

