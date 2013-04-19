// 动画列表
ANIMATIONS = ['fade', 'moveTop', 'moveBottom', 'moveLeft', 'moveRight', 'scale'];
ANIMATION_TOTAL = ANIMATIONS.length;

// 效果
function fx( _fx ) {
	// 增加随机延迟
	fxApplyRandomDelay(_fx);
}


// 给予一个随机延迟
function fxApplyRandomDelay(fx) {
	var bb = BUFFER_BACK, bc = BUFFER_CURRENT;
	for( var i = 0; i < CUBE_TOTAL; i++ ) {
		// 生成一个随机delay
		var delay = Math.random() * .6,
			duration = DURATION + Math.random() - .5;
		// 带效果！
		bc.eq(i).css({
			'webkitAnimation': fx + 'In ' + duration + 's ease ' + delay + 's 1',
			'animation': fx + 'In ' + duration + 's ease ' + delay + 's 1'
		});
		bb.eq(i).css({
			'webkitAnimation': fx + 'Out ' + duration + 's ease ' + delay + 's 1',
			'animation': fx + 'Out ' + duration + 's ease ' + delay + 's 1'
		});

		// 更换前后层关系
		setTimeout(function(){
			bb.css('zIndex', 1);
			bc.css('zIndex', 3);
		}, (duration + delay) * 1000);
	}
}

// 生成随机数
function random(range) {
  return Math.floor( Math.random() * range );
}