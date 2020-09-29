import functools
import time
import traceback
from bluepy.btle import BTLEDisconnectError
from .exception import RedmondKettleException, RedmondKettleConnectException

def iteration_decorator(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        self = args[0]
        result = False
        iter = 0
        while iter < 100:
            iter = iter + 1
            try:
                print('Call method', method, iter)
                result = method(*args, **kwargs)
                break
            except RedmondKettleException as e:
                self.log('!!!!!!!!!!!!!!!RedmondKettleException', e)
                print(traceback.format_exc())
                break
            except BTLEDisconnectError as e:
                self.log('!!!!!!!!!!!!BTLEDisconnectError', e)
                print(traceback.format_exc())
                raise RedmondKettleConnectException(str(e))
            except RedmondKettleConnectException as e:
                self.log('!!!!!!!!!!!!RedmondKettleConnectException', e)
                print(traceback.format_exc())
                raise e
            except Exception as e:
                self.log('!!!!!!!!!!!!Exception', e)
                print(traceback.format_exc())
                time.sleep(3)
                continue
        return result
    return wrapper