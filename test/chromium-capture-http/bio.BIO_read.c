int BIO_read(BIO *bio, void *buf, int len) {
  if (bio == NULL || bio->method == NULL || bio->method->bread == NULL) {
    OPENSSL_PUT_ERROR(BIO, BIO_R_UNSUPPORTED_METHOD);
    return -2;
  }
  if (!bio->init) {
    OPENSSL_PUT_ERROR(BIO, BIO_R_UNINITIALIZED);
    return -2;
  }
  if (len <= 0) {
    return 0;
  }
  int ret = bio->method->bread(bio, buf, len);
  if (ret > 0) {
    bio->num_read += ret;
  }
  return ret;
}
