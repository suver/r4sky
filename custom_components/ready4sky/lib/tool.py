import functools
import time
import traceback
from bluepy.btle import BTLEDisconnectError, BTLEInternalError
from .exception import RedmondKettleException, RedmondKettleConnectException

def iteration_decorator(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        self = args[0]
        result = False
        try:
            self.log('Call method', method, iter)
            result = method(*args, **kwargs)
        except RedmondKettleException as e:
            self.log('RedmondKettleException', e, error=True)
        except BTLEDisconnectError as e:
            self.log('BTLEDisconnectError', e, error=True)
        except RedmondKettleConnectException as e:
            self.log('RedmondKettleConnectException', e, error=True)
        except BTLEInternalError as e:
            self.log('Error:', e, error=True)
        except Exception as e:
            self.log('Exception', e, error=True)
        return result
    return wrapper

# def iteration_decorator(method):
#     @functools.wraps(method)
#     def wrapper(*args, **kwargs):
#         self = args[0]
#         result = False
#         iter = 0
#         while iter < 10:
#             iter = iter + 1
#             try:
#                 self.log('Call method', method, iter)
#                 result = method(*args, **kwargs)
#                 print(result)
#                 break
#             except RedmondKettleException as e:
#                 self.log('RedmondKettleException', e, error=True)
#                 break
#             except BTLEDisconnectError as e:
#                 self.log('BTLEDisconnectError', e, error=True)
#                 time.sleep(3)
#                 continue
#             except RedmondKettleConnectException as e:
#                 self.log('RedmondKettleConnectException', e, error=True)
#                 time.sleep(3)
#                 continue
#             except BTLEInternalError as e:
#                 self.log('Error:', e, error=True)
#                 time.sleep(3)
#                 continue
#             except Exception as e:
#                 self.log('Exception', e, error=True)
#                 time.sleep(3)
#                 continue
#         return result
#     return wrapper