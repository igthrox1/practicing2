import Header from "./header";

function bag() {
  return (
    <>
      <Header />
      <main>
        <div class="bag-page">
          <div class="bag-items-container"></div>
          <div class="bag-summary"></div>
        </div>
      </main>
      
      <Footer />
    </>
  );
}

export default bag;
