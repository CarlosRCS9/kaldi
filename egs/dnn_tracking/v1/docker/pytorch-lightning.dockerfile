FROM pytorch-lightning

RUN pip install jupyter

CMD ["sh", "-c", "jupyter notebook --no-browser --ip=0.0.0.0 --port=8888"]
