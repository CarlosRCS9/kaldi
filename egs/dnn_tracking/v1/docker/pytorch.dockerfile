FROM pytorch/pytorch:latest

RUN pip install matplotlib

RUN pip install jupyter
RUN mkdir -p /.local/share/jupyter
RUN chmod -R 777 /.local/share/jupyter

CMD ["sh", "-c", "jupyter notebook --no-browser --ip=0.0.0.0"]
