int BIO_write(BIO *bio, const void *in, int inl) {
  if (bio == NULL || bio->method == NULL || bio->method->bwrite == NULL) {
    OPENSSL_PUT_ERROR(BIO, BIO_R_UNSUPPORTED_METHOD);
    return -2;
  }
  if (!bio->init) {
    OPENSSL_PUT_ERROR(BIO, BIO_R_UNINITIALIZED);
    return -2;
  }
  if (inl <= 0) {
    return 0;
  }
  int ret = bio->method->bwrite(bio, in, inl);
  if (ret > 0) {
    bio->num_write += ret;
  }
  return ret;
}
