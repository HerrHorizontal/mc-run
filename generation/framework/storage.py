# -*- coding: utf-8 -*-
"""Verified storage of files on the remote storage element."""

import os
import uuid

from law.logger import get_logger

logger = get_logger(__name__)


def retry_remote(func, attempts=5, delay=30):
    """Call a function sending a request to the storage element, retrying it if it fails.

    Args:
        func (Callable): Function without arguments
        attempts (int): Maximum number of attempts
        delay (float): Seconds between attempts

    Returns:
        Return value of `func`
    """
    import time

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as e:
            if attempt == attempts:
                raise
            logger.warning(
                "Request to storage element failed ({}), retry {}/{} in {} s".format(
                    e, attempt, attempts - 1, delay
                )
            )
            time.sleep(delay)


def remote_rename(src, dst):
    """Rename a remote WLCG file target on the storage element, without copying the data.

    Args:
        src (law.wlcg.WLCGFileTarget): Remote file target to rename
        dst (law.wlcg.WLCGFileTarget): New remote file target on the same storage element
    """
    file_interface = src.fs.file_interface

    def rename():
        # a failed attempt may have renamed the file nevertheless
        if dst.exists() and not src.exists():
            return
        with file_interface.context() as ctx:
            ctx.rename(src.uri(base_name="stat"), dst.uri(base_name="stat"))

    retry_remote(rename)


def adler32_checksum(file_path, block_size=16 * 1024 * 1024):
    """Compute the ADLER32 checksum of a local file, as used by dCache.

    Args:
        file_path (str): Path of the local file
        block_size (int): Number of bytes read at once

    Returns:
        int: ADLER32 checksum
    """
    import zlib

    checksum = 1
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            checksum = zlib.adler32(block, checksum)
    return checksum & 0xFFFFFFFF


def remote_adler32_checksum(target):
    """Get the ADLER32 checksum of a remote WLCG file target from the storage element.

    Args:
        target (law.wlcg.WLCGFileTarget): Remote file target

    Returns:
        int: ADLER32 checksum
    """
    file_interface = target.fs.file_interface

    def checksum():
        with file_interface.context() as ctx:
            return int(ctx.checksum(target.uri(base_name="stat"), "ADLER32"), 16)

    return retry_remote(checksum)


def store_verified(local_path, output):
    """Upload a local file to a remote WLCG file target and verify the stored file.

    The file is uploaded under a temporary name, unique to this job, and renamed only after its
    size and ADLER32 checksum on the storage element match the local file, so an incomplete
    upload never gets the output name.

    Args:
        local_path (str): Path of the local file
        output (law.wlcg.WLCGFileTarget): Remote file target to store the file at

    Raises:
        IOError: The stored file differs from the local file
    """
    local_size = os.path.getsize(local_path)
    local_checksum = adler32_checksum(local_path)
    tmp_output = output.sibling(
        "{}.{}.tmp".format(output.basename, uuid.uuid4().hex[:8]), type="f"
    )
    try:
        tmp_output.copy_from_local(local_path, cache=False)
        stored_size = tmp_output.stat().st_size
        stored_checksum = remote_adler32_checksum(tmp_output)
        if stored_size != local_size or stored_checksum != local_checksum:
            raise IOError(
                "Stored file {} ({} bytes, ADLER32 {:08x}) differs from local file "
                "({} bytes, ADLER32 {:08x})! Abort!".format(
                    tmp_output.uri(),
                    stored_size,
                    stored_checksum,
                    local_size,
                    local_checksum,
                )
            )
        logger.info(
            "Verified ADLER32 checksum {:08x} of {}".format(local_checksum, tmp_output.uri())
        )
        if output.exists():
            # another job of the same branch stored the output in the meantime
            logger.warning("Output {} exists already, keeping it".format(output.uri()))
            tmp_output.remove()
            return
        remote_rename(tmp_output, output)
    except BaseException:
        # the cleanup must not hide the original error
        try:
            if tmp_output.exists():
                logger.error("Removing incomplete upload {}".format(tmp_output.uri()))
                tmp_output.remove()
        except Exception as e:
            logger.error("Removing {} failed: {}".format(tmp_output.uri(), e))
        raise
    if output.stat().st_size != local_size:
        raise IOError("Renamed file {} has an unexpected size! Abort!".format(output.uri()))
    logger.info("Stored {}".format(output.uri()))
