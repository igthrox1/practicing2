import BagItem from "../components/bagItem.jsx";
import BagSummary from "../components/bagSummary.jsx";
import { useSelector } from "react-redux";

function bag() {
  const bagItems = useSelector((store) => store.bag);
  const items = useSelector((store) => store.items);
  const finalItems = items.filter((item) => {
    const itemIndex = bagItems.indexOf(item.id);
    return itemIndex >= 0;
  });

  return (
    <>
      <main>
        <div class="bag-page">
          <div class="bag-items-container">
            {finalItems.map((item) => (
              <BagItem item={item} />
            ))}
          </div>
          <BagSummary />
        </div>
      </main>
    </>
  );
}

export default bag;
