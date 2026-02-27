"""录制器相关路由"""


class RecorderRoutes:
    """录制器路由"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def start(self):
        """POST /api/v1/recorder/start - 开始录制"""
        if not hasattr(self.app, '_recorder'):
            from ...core.recorder import InputRecorder
            self.app._recorder = InputRecorder()
        self.app._recorder.start()
        self.handler._ok({'status': 'recording'})
        self.handler._log_request('POST', '/recorder/start', 200)

    def stop(self):
        """POST /api/v1/recorder/stop - 停止录制并返回步骤"""
        if not hasattr(self.app, '_recorder'):
            self.handler._ok({'steps': [], 'count': 0})
            self.handler._log_request('POST', '/recorder/stop', 200)
            return
        self.app._recorder.stop()
        steps = self.app._recorder.to_steps()
        self.handler._ok({'steps': steps, 'count': len(steps)})
        self.handler._log_request('POST', '/recorder/stop', 200)

    def pause(self):
        """POST /api/v1/recorder/pause - 暂停/恢复录制"""
        if hasattr(self.app, '_recorder'):
            self.app._recorder.pause()
        self.handler._ok({'status': 'paused' if self.app._recorder._paused else 'recording'})
        self.handler._log_request('POST', '/recorder/pause', 200)

    def status(self):
        """GET /api/v1/recorder/status - 获取录制状态"""
        if not hasattr(self.app, '_recorder'):
            self.handler._ok({'recording': False, 'paused': False, 'event_count': 0})
            self.handler._log_request('GET', '/recorder/status', 200)
            return
        self.handler._ok({
            'recording': self.app._recorder.is_recording,
            'paused': self.app._recorder._paused,
            'event_count': self.app._recorder.event_count
        })
        self.handler._log_request('GET', '/recorder/status', 200)
